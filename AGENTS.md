# Instructions for AI Agents

Welcome! If you are an AI agent working on this repository, please review these instructions to understand the stack and workflows for this project.

## Tech Stack
* **Java:** Build with JDK 25 for current Minecraft compatibility probes. The project currently emits Java 21 bytecode via `maven.compiler.release`.
* **Build Tool:** Apache Maven 3.9.16, pinned by Apache Maven Wrapper 3.3.4. Use `./mvnw` (or `mvnw.cmd` on Windows) rather than a system Maven installation.

## Build Instructions
This project uses GitHub Packages to download the `Bridge` dependency. When running a build locally or within an automated environment, you must provide authentication.

### Authentication
To build the project, you need a GitHub Personal Access Token (PAT) with `read:packages` scope.
1. Provide the token via the `GITHUB_TOKEN` environment variable.
2. (Optional) Provide the `GITHUB_ACTOR` environment variable with your GitHub username.

Example of setting up authentication locally:
```sh
export GITHUB_TOKEN=your-personal-access-token
export GITHUB_ACTOR=your-github-username
```
(See `.env.example` in the root of the repository for reference).

### Compiling and Verifying
If you need to fetch the latest exact `Bridge` version, use the provided script:
```sh
export BRIDGE_VERSION=$(./scripts/resolve-bridge-version.sh)
```
Then run the canonical build:
```sh
./mvnw -B verify
```

For a reproducible build or release investigation, provide the exact recorded `BRIDGE_VERSION` rather than allowing a moving snapshot to resolve again.

To quickly check if everything compiles:
```sh
./mvnw -B clean compile
```

To run tests:
```sh
./mvnw -B test
```

On Windows, use the equivalent `mvnw.cmd` commands.

## Build and Compatibility Discipline
* Do not bypass the Maven Wrapper or change its pinned Maven version without updating the versioning/modernization documentation and CI evidence.
* Do not modify generated build artifacts directly.
* Packaging/toolchain changes must preserve the artifact contract in `scripts/verify-artifact-contract.sh` and pass the focused current-stable Minecraft patch + boot compatibility gate.
* Keep `Bridge` and VanillaCord independently versioned; record the exact Bridge coordinate consumed by each VanillaCord artifact.
* Ensure proper testing and verification after modifying the codebase.
* Look for `AGENTS.md` files in nested directories (if any are added in the future) for more specific instructions.
