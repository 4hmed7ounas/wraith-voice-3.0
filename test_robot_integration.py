"""
Integration Test Suite for Voice-Controlled Robot
Tests HTTP communication between voice bot and robot controller
"""

import asyncio
import httpx
import os
from dotenv import load_dotenv
from loguru import logger

load_dotenv(override=True)

ROBOT_URL = os.getenv("ROBOT_CONTROLLER_URL", "http://192.168.1.100:5000")
TIMEOUT = 5.0


class RobotIntegrationTester:
    """Test suite for robot controller integration"""

    def __init__(self, robot_url: str):
        self.robot_url = robot_url
        self.client = httpx.AsyncClient(timeout=TIMEOUT)
        self.tests_passed = 0
        self.tests_failed = 0

    async def test_connection(self) -> bool:
        """Test 1: Check if robot controller is online"""
        print("\n[TEST 1] Testing robot controller connection...")
        try:
            response = await self.client.get(f"{self.robot_url}/")
            if response.status_code == 200:
                print(f"  ✅ PASS: Robot controller is online")
                print(f"     Response: {response.text.strip()}")
                self.tests_passed += 1
                return True
            else:
                print(f"  ❌ FAIL: Unexpected status code {response.status_code}")
                self.tests_failed += 1
                return False
        except Exception as e:
            print(f"  ❌ FAIL: Connection error - {e}")
            print(f"     Make sure robot_controller.py is running at {self.robot_url}")
            self.tests_failed += 1
            return False

    async def test_movement_command(self, direction: str) -> bool:
        """Test movement in a specific direction"""
        print(f"\n[TEST] Testing {direction} movement...")
        try:
            # Send start command
            start_cmd = f"{direction}_start"
            response = await self.client.post(
                f"{self.robot_url}/control",
                content=start_cmd
            )

            if response.status_code != 200:
                print(f"  ❌ FAIL: Start command failed - {response.text}")
                self.tests_failed += 1
                return False

            print(f"  ✅ Start command sent: {start_cmd}")

            # Wait briefly
            await asyncio.sleep(0.5)

            # Send stop command
            stop_cmd = f"{direction}_stop"
            response = await self.client.post(
                f"{self.robot_url}/control",
                content=stop_cmd
            )

            if response.status_code != 200:
                print(f"  ❌ FAIL: Stop command failed - {response.text}")
                self.tests_failed += 1
                return False

            print(f"  ✅ Stop command sent: {stop_cmd}")
            print(f"  ✅ PASS: {direction.upper()} movement test successful")
            self.tests_passed += 1
            return True

        except Exception as e:
            print(f"  ❌ FAIL: {direction} movement error - {e}")
            self.tests_failed += 1
            return False

    async def test_all_movements(self) -> bool:
        """Test 2-5: Test all four movement directions"""
        print("\n[TEST 2-5] Testing all movement directions...")
        directions = ["forward", "backward", "left", "right"]
        all_passed = True

        for direction in directions:
            result = await self.test_movement_command(direction)
            all_passed = all_passed and result
            await asyncio.sleep(0.3)  # Brief pause between tests

        return all_passed

    async def test_speed_control(self) -> bool:
        """Test 6: Test speed increase/decrease"""
        print("\n[TEST 6] Testing speed control...")
        try:
            # Test speed increase
            response = await self.client.post(
                f"{self.robot_url}/control",
                content="speed+"
            )
            if response.status_code != 200:
                print(f"  ❌ FAIL: Speed increase failed")
                self.tests_failed += 1
                return False

            print(f"  ✅ Speed increased")

            # Test speed decrease
            response = await self.client.post(
                f"{self.robot_url}/control",
                content="speed-"
            )
            if response.status_code != 200:
                print(f"  ❌ FAIL: Speed decrease failed")
                self.tests_failed += 1
                return False

            print(f"  ✅ Speed decreased")
            print(f"  ✅ PASS: Speed control test successful")
            self.tests_passed += 1
            return True

        except Exception as e:
            print(f"  ❌ FAIL: Speed control error - {e}")
            self.tests_failed += 1
            return False

    async def test_distance_sensor(self) -> bool:
        """Test 7: Test distance sensor reading"""
        print("\n[TEST 7] Testing distance sensor...")
        try:
            response = await self.client.get(f"{self.robot_url}/get_distance")

            if response.status_code != 200:
                print(f"  ❌ FAIL: Distance sensor request failed")
                self.tests_failed += 1
                return False

            data = response.json()
            distance = data.get('distance', -1)

            if distance < 0:
                print(f"  ❌ FAIL: Invalid distance reading")
                self.tests_failed += 1
                return False

            print(f"  ✅ Distance reading: {distance:.2f} cm")
            print(f"  ✅ PASS: Distance sensor test successful")
            self.tests_passed += 1
            return True

        except Exception as e:
            print(f"  ❌ FAIL: Distance sensor error - {e}")
            self.tests_failed += 1
            return False

    async def test_auto_mode(self) -> bool:
        """Test 8: Test auto mode start/stop"""
        print("\n[TEST 8] Testing auto mode control...")
        try:
            # Start auto mode
            response = await self.client.post(
                f"{self.robot_url}/control",
                content="auto_start"
            )
            if response.status_code != 200:
                print(f"  ❌ FAIL: Auto mode start failed")
                self.tests_failed += 1
                return False

            print(f"  ✅ Auto mode started")
            await asyncio.sleep(2.0)  # Let it run briefly

            # Stop auto mode
            response = await self.client.post(
                f"{self.robot_url}/control",
                content="auto_stop"
            )
            if response.status_code != 200:
                print(f"  ❌ FAIL: Auto mode stop failed")
                self.tests_failed += 1
                return False

            print(f"  ✅ Auto mode stopped")
            print(f"  ✅ PASS: Auto mode test successful")
            self.tests_passed += 1
            return True

        except Exception as e:
            print(f"  ❌ FAIL: Auto mode error - {e}")
            self.tests_failed += 1
            return False

    async def test_timeout_handling(self) -> bool:
        """Test 9: Test timeout handling with invalid URL"""
        print("\n[TEST 9] Testing timeout/error handling...")
        try:
            bad_client = httpx.AsyncClient(timeout=1.0)
            bad_url = "http://192.168.255.255:5000"  # Non-existent IP

            try:
                await bad_client.get(f"{bad_url}/")
                print(f"  ❌ FAIL: Should have timed out")
                self.tests_failed += 1
                return False
            except (httpx.TimeoutException, httpx.ConnectError):
                print(f"  ✅ Timeout/error handled correctly")
                print(f"  ✅ PASS: Error handling test successful")
                self.tests_passed += 1
                return True
            finally:
                await bad_client.aclose()

        except Exception as e:
            print(f"  ❌ FAIL: Timeout test error - {e}")
            self.tests_failed += 1
            return False

    async def run_all_tests(self):
        """Run complete test suite"""
        print("=" * 70)
        print("WRAITH Robot Integration Test Suite")
        print("=" * 70)
        print(f"Robot Controller URL: {self.robot_url}")
        print(f"Timeout: {TIMEOUT}s")
        print("=" * 70)

        # Test 1: Connection
        connection_ok = await self.test_connection()

        if not connection_ok:
            print("\n" + "=" * 70)
            print("⚠️  CRITICAL: Cannot connect to robot controller")
            print("   Please ensure:")
            print("   1. robot_controller.py is running on Raspberry Pi")
            print(f"   2. Robot is accessible at {self.robot_url}")
            print("   3. Network connection is working")
            print("=" * 70)
            return

        # Run remaining tests only if connection works
        await self.test_all_movements()      # Tests 2-5
        await self.test_speed_control()      # Test 6
        await self.test_distance_sensor()    # Test 7
        await self.test_auto_mode()          # Test 8
        await self.test_timeout_handling()   # Test 9

        # Summary
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {self.tests_failed}")
        print(f"📊 Success Rate: {(self.tests_passed/(self.tests_passed+self.tests_failed)*100):.1f}%")
        print("=" * 70)

        if self.tests_failed == 0:
            print("🎉 ALL TESTS PASSED! Voice-robot integration is ready!")
        else:
            print("⚠️  Some tests failed. Please review and fix issues.")

        print("=" * 70)

        # Cleanup
        await self.client.aclose()


async def main():
    """Run integration tests"""
    tester = RobotIntegrationTester(ROBOT_URL)
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
