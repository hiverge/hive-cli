import subprocess

def buildImages(
    image: str,
    platforms: str = "linux/amd64,linux/arm64",
    context: str = ".",
    dockerfile: str = "Dockerfile",
    push: bool = False
):
    cmd = [
        "docker", "buildx", "build",
        "--platform", platforms,
        "--file", dockerfile,
        "--tag", image,
        context,
    ]
    if push:
        cmd.append("--push")

    subprocess.run(cmd, check=True)
