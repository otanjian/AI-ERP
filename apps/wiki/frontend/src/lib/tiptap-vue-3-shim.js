/**
 * TipTap Vue 3 Shim
 *
 * This shim re-exports all exports from @tiptap/vue-3 and adds the
 * BubbleMenu and FloatingMenu components that were moved to a subpath
 * in TipTap v3. This ensures compatibility with frappe-ui which expects
 * the v2 API where these were exported from the main package.
 *
 * Migration: In v3, menus moved from '@tiptap/vue-3' to '@tiptap/vue-3/menus'
 */

// Import everything from the actual @tiptap/vue-3 package
// Using the ?original query to bypass the alias
import * as TiptapVue3 from '@tiptap/vue-3?original';

// Re-export everything from @tiptap/vue-3
export const {
	Editor,
	EditorContent,
	NodeViewContent,
	NodeViewWrapper,
	VueNodeViewRenderer,
	VueRenderer,
	useEditor,
	nodeViewProps,
	markViewProps,
	VueMarkViewRenderer,
	MarkViewContent,
} = TiptapVue3;

// Re-export everything from @tiptap/core (which @tiptap/vue-3 also re-exports)
export * from '@tiptap/core';

// Import and re-export BubbleMenu and FloatingMenu from their new v3 location
// Using ?original to bypass the alias that points to this shim
export { BubbleMenu, FloatingMenu } from '@tiptap/vue-3/menus?original';
