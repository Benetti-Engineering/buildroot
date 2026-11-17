/*
 * Simple HTTP server using the mongoose library.
 *
 * Usage: mongoose-test <listen-url> <root-dir>
 *
 * - GET /api/hello returns a fixed JSON object
 * - POST /api/sum with a JSON body {"a": x, "b": y} returns their sum
 * - any other URI is served from <root-dir>
 */

#include "mongoose.h"

static const char *root_dir;

static void handler(struct mg_connection *c, int ev, void *ev_data)
{
	struct mg_http_message *hm;

	if (ev != MG_EV_HTTP_MSG)
		return;

	hm = (struct mg_http_message *) ev_data;
	if (mg_match(hm->uri, mg_str("/api/hello"), NULL)) {
		mg_http_reply(c, 200, "Content-Type: application/json\r\n",
			      "{%m:%m}\n", MG_ESC("message"),
			      MG_ESC("Hello Buildroot"));
	} else if (mg_match(hm->uri, mg_str("/api/sum"), NULL)) {
		long a = mg_json_get_long(hm->body, "$.a", 0);
		long b = mg_json_get_long(hm->body, "$.b", 0);

		mg_http_reply(c, 200, "Content-Type: application/json\r\n",
			      "{%m:%ld}\n", MG_ESC("sum"), a + b);
	} else {
		struct mg_http_serve_opts opts = { .root_dir = root_dir };

		mg_http_serve_dir(c, hm, &opts);
	}
}

int main(int argc, char *argv[])
{
	struct mg_mgr mgr;

	if (argc != 3) {
		fprintf(stderr, "Usage: %s <listen-url> <root-dir>\n", argv[0]);
		return 1;
	}
	root_dir = argv[2];

	mg_log_set(MG_LL_ERROR);
	mg_mgr_init(&mgr);
	if (mg_http_listen(&mgr, argv[1], handler, NULL) == NULL) {
		fprintf(stderr, "Cannot listen on %s\n", argv[1]);
		return 1;
	}
	for (;;)
		mg_mgr_poll(&mgr, 1000);

	return 0;
}
