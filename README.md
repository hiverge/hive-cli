# Hive-CLI

Hive-CLI is a command-line interface for managing and deploying the Hive agent and experiments on Kubernetes and other platforms.

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
- [docker](https://www.docker.com/) for image building.
- [gcloud CLI](https://cloud.google.com/sdk/docs/install) via `brew install gcloud` for authentication.

**Notes**:

- Make sure to enable the `✅ Use containerd for pulling and storing images` option in Docker Desktop settings, which is required for multi-arch image support.

### Install via pip

```bash
pip install hiverge-cli
```

### Install from source

```bash
source start.sh
```

## How to run

**Note**: Hive-CLI reads the configuration from a yaml file, by default it will look for the `~/.hive/hive.yaml`. You can also specify a different configuration file using the `-f` option. Refer to the [hive.yaml](./hive.yaml) for examples.

Below we assume that you have a `~/.hive/hive.yaml` file.

### Verify the version

```bash
hive version
```


### Edit the experiment

`Edit` command will open the configuration file in your default editor (e.g., vim, nano, etc.) for you to modify the experiment configuration. You can also specify a different editor using the `EDITOR` environment variable, by default it will use `vim`.

```bash
hive edit config
```

### Create an experiment

```bash
hive create exp my-experiment
```

*Note: This will build a Docker image for the experiment and push it to the container registry which may take some time, based on the Dockerfile and network speed. You can enable the Debug mode in the configuration file to see more detailed logs.*

### List experiments

```bash
hive show exps
```

### Visit Dashboard

```bash
hive dashboard
```

### Show logs

Sandboxes are the isolated environments where experiments run in parallel. You can list all the sandboxes and view their logs.

```bash
hive show sands
hive log <sandbox-name>
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

## Troubleshooting

See the [Troubleshooting Guide](docs//TROUBLESHOOTING.md) for common issues and solutions.
