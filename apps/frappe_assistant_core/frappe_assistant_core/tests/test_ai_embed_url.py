import unittest


class TestAIEmbedUrl(unittest.TestCase):
	def test_default_ai_assistant_embed_url_uses_previous_public_agent(self):
		from frappe_assistant_core.boot_extension import DEFAULT_AI_ASSISTANT_EMBED_URL

		self.assertEqual(
			DEFAULT_AI_ASSISTANT_EMBED_URL,
			"https://ai.bosofts.com/agents/3a6420a3-8bbe-40a1-8da2-4c6aad83b487/6d752020a22b48ad4a5b5b651cd48fa5181fee135776e9f2b20d4e0645f93d72",
		)


if __name__ == "__main__":
	unittest.main()
