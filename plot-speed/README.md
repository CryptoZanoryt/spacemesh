# plot-speed

Measure progress of your SpaceMesh smesher.

This was taken from the original `plot_speed.sh` and was augmented to add:
* additional statistics output
* realtime and average rates
* support of multiple plot segment files created by multi-GPU generation by multiple instances of `postcli`

## Usage

1. Clone the repository.

    ```git clone https://github.com/CryptoZanoryt/spacemesh```

2. Change to the new clone path.

    `cd spacemesh/plot-speed`

3. Run!

    On Linux/MacOS:

    `./plot_speed.sh`

    On Windows:

    `.\plot_speed.bat`
