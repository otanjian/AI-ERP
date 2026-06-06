/**
 * Shim for @tiptap/extension-table
 * Provides default export for frappe-ui compatibility with TipTap v3
 */
import { Table } from '@tiptap/extension-table';
export default Table;
export {
	Table,
	TableRow,
	TableCell,
	TableHeader,
} from '@tiptap/extension-table';
