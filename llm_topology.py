import llm
import httpx
import json
import click
from pathlib import Path

@llm.hookimpl
def register_commands(cli):
    @cli.group()
    def partition():
        """Manage partition settings for TopologyModel."""
        pass

    @partition.command(name="add")
    @click.argument("name")
    @click.argument("partition_id")
    def add_partition(name, partition_id):
        """Add a new partition with a name."""
        partitions = load_partitions()
        partitions[name] = partition_id
        save_partitions(partitions)
        click.echo(f"Partition '{name}' added with ID: {partition_id}")

    @partition.command(name="set")
    @click.argument("name")
    def set_partition(name):
        """Set the active partition by name."""
        partitions = load_partitions()
        if name not in partitions:
            raise click.ClickException(f"Partition '{name}' not found. Use 'llm partition add <name> <partition_id>' to add one.")
        set_active_partition(name)
        click.echo(f"Active partition set to: {name}")

    @partition.command(name="get")
    def get_partition():
        """Get the current active partition."""
        active_partition_file = get_active_partition_file()
        if active_partition_file.exists():
            active_partition = active_partition_file.read_text().strip()
            partitions = load_partitions()
            if active_partition in partitions:
                partition_id = partitions[active_partition]
                click.echo(f"Current active partition: {active_partition} (ID: {partition_id})")
            else:
                click.echo(f"Active partition '{active_partition}' not found in partitions.")
        else:
            click.echo("No active partition set.")

    @partition.command(name="list")
    def list_partitions():
        """List all partitions."""
        partitions = load_partitions()
        if not partitions:
            click.echo("No partitions added.")
            return
        for name, partition_id in partitions.items():
            click.echo(f"{name}: {partition_id}")

def get_partitions_file():
    user_directory = llm.user_dir()
    return user_directory / "partitions.json"

def get_active_partition_file():
    user_directory = llm.user_dir()
    return user_directory / "active_partition.txt"

def load_partitions():
    partitions_file = get_partitions_file()
    if partitions_file.exists():
        return json.loads(partitions_file.read_text())
    return {}

def save_partitions(partitions):
    partitions_file = get_partitions_file()
    partitions_file.write_text(json.dumps(partitions, indent=4))

def set_active_partition(name):
    active_partition_file = get_active_partition_file()
    active_partition_file.write_text(name)

@llm.hookimpl
def register_models(register):
    register(TopologyModel("topology-tiny"))
    register(TopologyModel("topology-small"))
    register(TopologyModel("topology-medium"))

class TopologyModel(llm.Model):
    needs_key = "topology"
    key_env_var = "TOPOLOGY_API_KEY"
    can_stream = True

    def __init__(self, model_id):
        self.model_id = model_id

    def build_messages(self, prompt, conversation):
        if not conversation:
            return [{"role": "user", "content": prompt.prompt}]
        messages = []
        for response in conversation.responses:
            messages.append({"role": "user", "content": response.prompt.prompt})
            messages.append({"role": "assistant", "content": response.text()})
        messages.append({"role": "user", "content": prompt.prompt})
        return messages

    def execute(self, prompt, stream, response, conversation):
        api_key = self.get_key()
        api_base = "https://topologychat.com/api"
        headers = {"Authorization": f"Bearer {api_key}"}
        active_partition_file = get_active_partition_file()
        if not active_partition_file.exists():
            raise click.ClickException("No active partition set. Use 'llm partition set <name>' to set one.")
        active_partition = active_partition_file.read_text().strip()
        partitions = load_partitions()
        if active_partition not in partitions:
            raise click.ClickException(f"Active partition '{active_partition}' not found in partitions.")
        partition_id = partitions[active_partition]
        data = {
            "partition_id": partition_id,
            "messages": self.build_messages(prompt, conversation),
            "stream": stream,
        }
        if prompt.system:
            data["system"] = prompt.system

        if stream:
            try:
                with httpx.stream(
                    "POST",
                    f"{api_base}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=None,
                ) as stream:
                    first_chunk = True
                    for chunk in stream.iter_lines():
                        if first_chunk:
                            first_chunk = False
                            continue  # Skip the first chunk

                        if chunk:
                            try:
                                # Strip the 'data: ' prefix
                                json_chunk = chunk.replace('data: ', '')
                                data = json.loads(json_chunk)
                                if (
                                    "choices" in data
                                    and len(data["choices"]) > 0
                                    and "delta" in data["choices"][0]
                                    and "content" in data["choices"][0]["delta"]
                                ):
                                    content = data["choices"][0]["delta"]["content"]
                                    if content:
                                        yield content
                            except json.JSONDecodeError as e:
                                print(f"Error decoding JSON: {e}")
                                print(f"Raw chunk: {chunk}")  # Print the raw chunk for debugging
                                # Handle the error appropriately
            except httpx.ConnectError as e:
                print(f"Connection Error: {e}")
                # Handle the error appropriately
            except httpx.ReadTimeout as e:
                print(f"Read Timeout: {e}")
                # Handle the error appropriately
        else:
            try:
                response_data = httpx.post(
                    f"{api_base}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=None,
                )
                response_data.raise_for_status()
                response.response_json = response_data.json()
                yield response_data.json()["choices"][0]["message"]["content"]
            except httpx.HTTPStatusError as e:
                print(f"HTTP Error: {e}")
                # Handle the error appropriately
