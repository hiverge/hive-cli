import subprocess

def build_image(
    image: str,
    platforms: str = "linux/amd64,linux/arm64",
    context: str = ".",
    dockerfile: str = "Dockerfile",
    push: bool = False
):
    cmd = [
        "docker", "build",
        "--platform", platforms,
        "--file", dockerfile,
        "--tag", image,
        context,
    ]
    if push:
        cmd.append("--push")

    try:
        subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        print("Build STDERR:\n", e.stderr)
        raise
