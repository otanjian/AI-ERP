# Copyright (C) 2025 Paul Clinton
# SPDX-License-Identifier: AGPL-3.0-only

import frappe

DEFAULT_AI_ASSISTANT_EMBED_URL = (
	"http://localhost:4091/agents/5130f0df-023a-4014-afad-f4533e2b10d1/"
	"57f9d4480c5d5d47f89c47b126f092bcd18f8c9d8e6c143e8479a9c7a29c9479"
)


def _get_ai_assistant_embed_url() -> str:
	return frappe.conf.get("ai_assistant_embed_url") or DEFAULT_AI_ASSISTANT_EMBED_URL


def extend_desk_boot_ai_assistant(*, bootinfo):
	bootinfo["ai_assistant_embed_url"] = _get_ai_assistant_embed_url()


def extend_website_boot_ai_assistant(context):
	boot = context.get("boot")
	if isinstance(boot, dict):
		boot["ai_assistant_embed_url"] = _get_ai_assistant_embed_url()
