# Troubleshooting Guide

**Q: I want to build a sandbox image with private dependencies. How can I do that?**

**A:** We use Docker BuildKit secrets to securely embed your private dependencies during the build process. Here's how you can do it:

1. **Create secret environment variable**: Set an environment variable in your shell that contains the secret value. For example, if you're using a GitHub token to access private repositories, you can set it like this:

    ```bash
    export GITHUB_TOKEN=your_github_token_here
    ```

2. **Pass the secret in Hive-CLI config yaml**:

    ```yaml
    sandbox:
        build_secret: GITHUB_TOKEN
    ```

3. **Update your Dockerfile**: Make sure your Dockerfile is set up to use the build secret. You can use the `RUN --mount=type=secret,id=mysecret` syntax to access the secret in your build steps. Here's an example snippet of a Dockerfile that uses a GitHub token to install private dependencies:

    ```Dockerfile

    # FROM command here.

    # Step-1: Install the git package.
    RUN apt-get update && apt-get install -y git curl ca-certificates && rm -rf /var/lib/apt/lists/*

    # Other commands here.

    # Step-2: Use the secret to access private repositories. Here's an example of installing Python packages from a private GitHub repository with the secret named GITHUB_TOKEN.
    # REPLACE the 'uv pip install' command with your actual installation command.
    RUN --mount=type=secret,id=GITHUB_TOKEN \
        export GITHUB_TOKEN=$(cat /run/secrets/GITHUB_TOKEN) && \
        git config --global url."https://${GITHUB_TOKEN}@github.com/".insteadOf "https://github.com/" && \
        uv pip install --system --requirement pyproject.toml \
        git config --global --unset url."https://${GITHUB_TOKEN}@github.com/".insteadOf

    # Other commands here.

    ```

This will make the secret available during the build process, allowing you to install private dependencies without exposing sensitive information.
