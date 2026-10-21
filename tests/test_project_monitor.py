import pathlib, sys, unittest
from unittest.mock import Mock, patch
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
import project_monitor as m

class MonitorTests(unittest.TestCase):
    def test_success_is_healthy(self):
        response=Mock(status_code=200,url="https://app.test/")
        with patch.object(m.requests,"get",return_value=response):
            self.assertEqual(m.check_url("https://app.test/")["status"],"ok")
    def test_server_error_is_high_severity(self):
        response=Mock(status_code=503,url="https://app.test/")
        with patch.object(m.requests,"get",return_value=response):
            result=m.check_url("https://app.test/")
        self.assertEqual(result["severity"],"high"); self.assertEqual(result["http_status"],503)
    def test_client_error_is_medium_severity(self):
        response=Mock(status_code=404,url="https://app.test/")
        with patch.object(m.requests,"get",return_value=response):
            result=m.check_url("https://app.test/")
        self.assertEqual(result["severity"],"medium")
    def test_invalid_scheme_rejected_without_request(self):
        with patch.object(m.requests,"get") as get:
            result=m.check_url("javascript:alert(1)")
        get.assert_not_called(); self.assertEqual(result["status"],"error")
    def test_network_failure_is_incident(self):
        with patch.object(m.requests,"get",side_effect=m.requests.Timeout()):
            result=m.check_url("https://app.test/")
        self.assertEqual(result["status"],"incident"); self.assertEqual(result["severity"],"high")

if __name__=="__main__": unittest.main()
