## Installation Procedure

To install the necessary dependencies, follow these steps:

1. **Run the Installation Script**
    - Navigate to the project directory.
    - Execute the `install.bat` script by double-clicking it or running the following command in the terminal:
      ```sh
      ./install.bat
      ```

## Configuration and Verification

1. **Configure the Environment**
    - Open Visual Studio Code (VSCode).
    - Ensure that the Python extension is installed.
    - Open the project folder in VSCode.
    - alternatively in shell goto <root>/python folder and
      ```sh
      code .
      ```

2. **Verify the Installation**
    - Open the integrated terminal in VSCode.
    - Run the following command to execute the tests:
      ```sh
      python -m unittest discover
      ```
    - Check the output to ensure all tests pass successfully.

By following these steps, you will have installed and verified the setup for the project.