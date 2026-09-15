import subprocess


rtl_file = "rtl/day1_test.v"

output_file = (
    "results/day1_python_sim.out"
)


compile_command = [

    "iverilog",

    "-o",
    output_file,

    rtl_file

]


print(
    "Compiling Verilog..."
)


compile_result = subprocess.run(

    compile_command,

    capture_output=True,

    text=True

)


if compile_result.returncode != 0:

    print(
        "COMPILATION FAIL"
    )

    print(
        compile_result.stderr
    )

    raise SystemExit(1)


print(
    "COMPILATION PASS"
)


run_result = subprocess.run(

    [
        "vvp",
        output_file
    ],

    capture_output=True,

    text=True

)


print(
    "\nSIMULATION OUTPUT"
)


print(
    run_result.stdout
)


if run_result.returncode == 0:

    print(
        "PYTHON SIMULATION CONTROL: PASS"
    )

else:

    print(
        "PYTHON SIMULATION CONTROL: FAIL"
    )
