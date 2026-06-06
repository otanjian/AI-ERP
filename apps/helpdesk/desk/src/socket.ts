import { io } from "socket.io-client";
import { socketio_port } from "../../../../sites/common_site_config.json";

// extend window object
declare global {
  interface Window {
    site_name: string;
  }
}

function get_socket_url(siteName: string): string {
	// Production: connect via the same origin so Nginx (or another reverse proxy)
	// can forward `/socket.io` to the Node realtime service.
	//
	// The previous logic used `http(s)://host:9000/...` whenever `location.port`
	// was set (e.g. custom HTTP ports), which breaks for public sites because
	// port 9000 is usually not exposed — browsers see ERR_CONNECTION_REFUSED.
	const { hostname, port } = window.location;
	const use_direct_socket_port =
		(hostname === "localhost" || hostname === "127.0.0.1") &&
		(port === "8000" || port === "8080");

	if (use_direct_socket_port) {
		return `http://${hostname}:${socketio_port}/${siteName}`;
	}

	return `${window.location.origin}/${siteName}`;
}

export function initSocket() {
	const siteName = window.site_name || window.location.hostname;
	const url = get_socket_url(siteName);

	const socket = io(url, {
		withCredentials: true,
		reconnectionAttempts: 5,
		...(window.location.protocol === "https:" ? { secure: true } : {}),
	});

	return socket;
}

export const socket = initSocket();
