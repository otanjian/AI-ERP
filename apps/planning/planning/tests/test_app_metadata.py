import unittest


class TestAppMetadata(unittest.TestCase):
    def test_app_metadata_declares_planning_app(self):
        from planning import __version__
        from planning import hooks

        self.assertTrue(__version__)
        self.assertEqual(hooks.app_name, "planning")
        self.assertEqual(hooks.app_title, "Planning")
        self.assertEqual(hooks.app_publisher, "Bosofts")


if __name__ == "__main__":
    unittest.main()
