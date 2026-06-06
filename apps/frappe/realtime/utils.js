const { get_conf } = require("../node_utils");
const conf = get_conf();

function get_url(socket, path) {
	if (!path) {
		path = "";
	}
	let url = socket.request.headers.origin;
	if (conf.developer_mode && url) {
		// Only rewrite for typical local dev (http://localhost:8080 → gunicorn port).
		// The old split(":") logic breaks HTTPS origins without an explicit port
		// (e.g. https://example.com → https:////example.com:8000) and makes fetch() fail.
		try {
			const u = new URL(url);
			const is_local =
				u.hostname === "localhost" ||
				u.hostname === "127.0.0.1" ||
				u.hostname === "[::1]";
			if (is_local && u.protocol === "http:" && conf.webserver_port) {
				u.port = String(conf.webserver_port);
				url = u.origin;
			}
		} catch {
			// leave url unchanged
		}
	}
	return url + path;
}

module.exports = {
	get_url,
};
