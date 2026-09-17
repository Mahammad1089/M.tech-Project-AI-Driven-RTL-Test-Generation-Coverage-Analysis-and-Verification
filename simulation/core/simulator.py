import subprocess
from pathlib import Path


class VerilogSimulator:

    def __init__(
        self,
        simulator="iverilog",
        runtime="vvp",
        timeout=30
    ):
        self.simulator = simulator
        self.runtime = runtime
        self.timeout = timeout


    def validate_file(self, file_path):

        path = Path(file_path)

        if not path.exists():
            return False

        if not path.is_file():
            return False

        return True


    def compile(
        self,
        rtl_file,
        testbench_file,
        output_file
    ):

        # Check whether RTL file exists
        if not self.validate_file(rtl_file):

            return {
                "status": "compile_error",
                "success": False,
                "message": (
                    f"RTL file not found: "
                    f"{rtl_file}"
                )
            }


        # Check whether testbench file exists
        if not self.validate_file(testbench_file):

            return {
                "status": "compile_error",
                "success": False,
                "message": (
                    f"Testbench file not found: "
                    f"{testbench_file}"
                )
            }


        # Create output directory if required
        output_path = Path(output_file)

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )


        # Icarus Verilog compilation command
        command = [
            self.simulator,
            "-o",
            str(output_file),
            str(rtl_file),
            str(testbench_file)
        ]


        # Run Icarus Verilog compiler
        result = subprocess.run(
            command,
            capture_output=True,
            text=True
        )


        # Return compilation information
        return {
            "status": (
                "compile_success"
                if result.returncode == 0
                else "compile_error"
            ),

            "success": (
                result.returncode == 0
            ),

            "return_code": (
                result.returncode
            ),

            "stdout": (
                result.stdout
            ),

            "stderr": (
                result.stderr
            ),

            "command": (
                command
            )
        }


    def simulate(
        self,
        output_file
    ):

        # VVP execution command
        command = [
            self.runtime,
            str(output_file)
        ]


        try:

            # Run the compiled Verilog simulation
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )


        except subprocess.TimeoutExpired:

            # Controlled failure if simulation
            # exceeds the configured timeout
            return {
                "status": "simulation_timeout",
                "success": False,
                "return_code": None,
                "stdout": "",
                "stderr": (
                    "Simulation exceeded timeout."
                ),
                "command": command
            }


        # Return normal simulation result
        return {
            "status": (
                "simulation_success"
                if result.returncode == 0
                else "simulation_error"
            ),

            "success": (
                result.returncode == 0
            ),

            "return_code": (
                result.returncode
            ),

            "stdout": (
                result.stdout
            ),

            "stderr": (
                result.stderr
            ),

            "command": (
                command
            )
        }


    def run(
        self,
        rtl_file,
        testbench_file,
        output_file
    ):

        # --------------------------------
        # STEP 1: Compile Verilog
        # --------------------------------

        compile_result = self.compile(
            rtl_file,
            testbench_file,
            output_file
        )


        # Stop if compilation failed
        if not compile_result["success"]:

            return {
                "overall_status": "FAIL",
                "stage": "compile",
                "compile": compile_result,
                "simulation": None
            }


        # --------------------------------
        # STEP 2: Run simulation
        # --------------------------------

        simulation_result = self.simulate(
            output_file
        )


        # Stop if simulation failed
        if not simulation_result["success"]:

            return {
                "overall_status": "FAIL",
                "stage": "simulation",
                "compile": compile_result,
                "simulation": simulation_result
            }


        # --------------------------------
        # STEP 3: Successful execution
        # --------------------------------

        return {
            "overall_status": "PASS",
            "stage": "complete",
            "compile": compile_result,
            "simulation": simulation_result
        }
