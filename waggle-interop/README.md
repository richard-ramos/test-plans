# Waggle Interop testing framework

## Overview

This framework is designed to reproducibly test the dissemination of
incrementally reconstructed objects over the
[Waggle protocol](https://github.com/libp2p/specs/pull/732) across different
implementations. It is heavily based on the
[GossipSub Interop framework](../gossipsub-interop) and leverages
[Shadow](https://shadow.github.io/) as its simulator.

There are two components to our interoperability test:

1. The _scenario_ we are running. This defines the specific instructions each node in
   the network takes at a specific point in time. Instructions such as publishing a
   piece, connecting to other nodes, or subscribing. See `script_instruction.py` for a
   list of instructions.
2. The _composition_ of the network. This defines what percent of the network is
   running what implementation.

A key aspect of this framework is that scenarios and compositions can be
modified without modifying implementations. See `experiment.py`, where this can be configured.

After running a test, the key result we extract from the simulation is the
_reliability_ of the object dissemination: the percentage of nodes that
successfully reconstructed each object (i.e. received all of its pieces).

Implementations are deemed interoperable if variations in composition do not
result in any significant differences in observed behavior or outputs. For
example, a network of all rust-libp2p nodes should behave the same as a network
with an even mix of rust-libp2p and go-libp2p nodes.

## Requirements

- [Shadow](https://shadow.github.io/) for shadow experiments.
- [uv](https://docs.astral.sh/uv/) for python dependencies.
- Implementation specific requirements for building the implementations (Rust, etc...)

## Running a simulation

```bash
uv run run.py --help
```

For example, to run a simulation of 32 rust-libp2p nodes:

```bash
uv run run.py --node_count 32 --composition rust --scenario "waggle"
```

The definitions of the experiment, composition, and scenarios are defined in `experiment.py`.

After running an experiment all the results and configuration needed to
reproduce the test are saved in an output folder which, by default, is named by
the specific scenario, node count, and composition. For the above example, the
output folder is `waggle-32-rust-<seed>-<timestamp>.data`.

## Running with Nim

Install Nim 2.2.10 and Nimble 0.24.1 alongside the Rust and Go toolchains needed
by `make binaries`. The pinned Rust peer requires Rust 1.98.1, and the pinned Go
peer requires Go 1.26. Shadow 3.3.0 was used for the initial Nim integration.

From this directory, run a mixed simulation and check the completion logs:

```bash
uv run run.py --node_count 8 --composition nim rust go --scenario waggle
uv run checks/dissimination.py latest --count 1
```

Use `--composition nim rust` or `--composition nim go` to test a pair, or
`--composition nim` for a Nim-only run. Use `--scenario waggle-sparse` for the
sparse topology. The runner builds all peers before starting Shadow.
Compositions are sampled randomly; inspect `latest/shadow.yaml` to confirm the
actual implementation mix, especially in small runs.

The Nim adapter lives in nim-libp2p and implements this framework's script and
piece format. The Makefile currently pins the adapter from
[iftech/nim-libp2p#3371](https://github.com/iftech/nim-libp2p/pull/3371), which
builds on the Waggle implementation in
[iftech/nim-libp2p#3349](https://github.com/iftech/nim-libp2p/pull/3349).
Both contributions are still under review. To build a different revision:

```bash
make binaries NIM_LIBP2P_REPO=https://github.com/iftech/nim-libp2p.git NIM_LIBP2P_REV=COMMIT_SHA
```

## Adding an implementation

To build the implementation reference `./test-specs/implementation.md`.

After implementing it, make sure to add build commands in the Makefile's `binaries` recipe.

Finally, add it to the `IMPLEMENTATIONS` dict in `experiment.py`.

## Examples

Minimal test of object dissemination

```bash
uv run run.py --node_count 2 --composition rust --scenario "waggle" && uv run checks/partial_messages.py latest/
```

That command runs the shadow simulation and then verifies the stdout logs have
the expected completion message.

## Tests

```bash
make test
```

This runs various shadow simulations and checks.

## Future work (contributions welcome)

- Add more scenarios.
- Add other implementations.
- Add more plots and visualizations.
- Add a helper to make it easier to rerun an experiment given an output folder.
- Add to CI
