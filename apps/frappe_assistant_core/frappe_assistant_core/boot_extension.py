# Copyright (C) 2025 Paul Clinton
# SPDX-License-Identifier: AGPL-3.0-only

import frappe

DEFAULT_AI_ASSISTANT_EMBED_URL = (
	"https://ai.bosofts.com/agents/3a6420a3-8bbe-40a1-8da2-4c6aad83b487/"
	"6d752020a22b48ad4a5b5b651cd48fa5181fee135776e9f2b20d4e0645f93d72"
)


def _get_ai_assistant_embed_url() -> str:
	return frappe.conf.get("ai_assistant_embed_url") or DEFAULT_AI_ASSISTANT_EMBED_URL


def extend_desk_boot_ai_assistant(*, bootinfo):
	bootinfo["ai_assistant_embed_url"] = _get_ai_assistant_embed_url()


def extend_website_boot_ai_assistant(context):
	boot = context.get("boot")
	if isinstance(boot, dict):
		boot["ai_assistant_embed_url"] = _get_ai_assistant_embed_url()
