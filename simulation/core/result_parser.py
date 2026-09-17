import re


class VerificationResultParser:

    def extract_integer(
        self,
        pattern,
        text
    ):

        match = re.search(
            pattern,
            text
        )

        if match:

            return int(
                match.group(1)
            )

        return None


    def parse(
        self,
        simulation_output
    ):

        total = self.extract_integer(

            r"TOTAL TESTS\s*=\s*(\d+)",

            simulation_output

        )


        passed = self.extract_integer(

            r"PASSED TESTS\s*=\s*(\d+)",

            simulation_output

        )


        failed = self.extract_integer(

            r"FAILED TESTS\s*=\s*(\d+)",

            simulation_output

        )


        if (
            total is None
            or passed is None
            or failed is None
        ):

            verification_status = (
                "UNKNOWN"
            )

        elif failed == 0:

            verification_status = (
                "PASS"
            )

        else:

            verification_status = (
                "FAIL"
            )


        return {

            "total_tests":
                total,

            "passed_tests":
                passed,

            "failed_tests":
                failed,

            "verification_status":
                verification_status

        }
