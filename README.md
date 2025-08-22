# Hive-CLI

Hive-CLI is a command-line interface for managing and deploying Hive agent and experiments on Kubernetes and other platforms.

```bash
     ███          █████   █████  ███
    ░░░███       ░░███   ░░███  ░░░
      ░░░███      ░███    ░███  ████  █████ █████  ██████
        ░░░███    ░███████████ ░░███ ░░███ ░░███  ███░░███
         ███░     ░███░░░░░███  ░███  ░███  ░███ ░███████
       ███░       ░███    ░███  ░███  ░░███ ███  ░███░░░
     ███░         █████   █████ █████  ░░█████   ░░██████
    ░░░          ░░░░░   ░░░░░ ░░░░░    ░░░░░     ░░░░░░
```

## Installation

### Pre-requisites

- Python 3.8 or higher
- [docker](https://www.docker.com/), for image building.
- [gcloud CLI](https://cloud.google.com/sdk/docs/install) via `brew install gcloud`

**Notes**:

- Make sure to enable the `✅ Use containerd for pulling and storing images` option in Docker Desktop settings, which is required for multi-arch image support.

### Install via pip (Not-Available Yet)

```bash
pip install hive-cli
```

### Install from source

```bash
source start.sh
```

## How to run

**Note**: Hive-CLI reads the configuration from a yaml file, by default it will look for the `~/.hive/sandbox-config.yaml`. You can also specify a different configuration file using the `-f` option. Refer to the [config.yaml](./config.yaml) for examples.

Below we assume that you have a `~/.hive/sandbox-config.yaml` file.

### Edit the experiment

`Edit` command will open the configuration file in your default editor (e.g., vim, nano, etc.) for you to modify the experiment configuration. You can also specify a different editor using the `EDITOR` environment variable, by default it will use `vim`.

```bash
hive edit config
```

### Create an experiment

```bash
hive create exp my-experiment
```

### List experiments

```bash
hive show exps
```

### Visit Dashboard

```bash
hive dashboard
```

### Delete an experiment


```bash
hive delete exp my-experiment
```

### More

See `hive -h` for more details.

## Development

### Debugging

Change the `log_level` in the configuration file to `DEBUG` to see more detailed logs.
