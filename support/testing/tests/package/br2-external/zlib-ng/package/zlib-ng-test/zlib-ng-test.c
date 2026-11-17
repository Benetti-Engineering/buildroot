/*
 * Test program for zlib-ng, built in zlib compatibility mode.
 *
 * Usage:
 *   zlib-ng-test version         print the library version
 *   zlib-ng-test selftest        run in-memory checks
 *   zlib-ng-test gzwrite <file>  compress stdin to a gzip file
 *   zlib-ng-test gzread <file>   uncompress a gzip file to stdout
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <zlib.h>

#define BUF_SIZE 16384

static int selftest(void)
{
	static const char check[] = "123456789";
	unsigned char src[65536], comp[70000], dst[65536];
	uLongf comp_len = sizeof(comp), dst_len = sizeof(dst);
	unsigned long crc, adler;
	size_t i;
	int level;

	/* Known check values for "123456789" */
	crc = crc32(0L, (const Bytef *)check, strlen(check));
	if (crc != 0xcbf43926UL) {
		fprintf(stderr, "crc32 mismatch: %08lx\n", crc);
		return 1;
	}
	adler = adler32(1L, (const Bytef *)check, strlen(check));
	if (adler != 0x091e01deUL) {
		fprintf(stderr, "adler32 mismatch: %08lx\n", adler);
		return 1;
	}

	/* Compressible pseudo-random data */
	srand(42);
	for (i = 0; i < sizeof(src); i++)
		src[i] = "Buildroot"[rand() % 9];

	for (level = Z_NO_COMPRESSION; level <= Z_BEST_COMPRESSION; level++) {
		comp_len = sizeof(comp);
		dst_len = sizeof(dst);
		if (compress2(comp, &comp_len, src, sizeof(src), level) != Z_OK) {
			fprintf(stderr, "compress2 failed at level %d\n", level);
			return 1;
		}
		if (level > Z_NO_COMPRESSION && comp_len >= sizeof(src)) {
			fprintf(stderr, "no compression at level %d\n", level);
			return 1;
		}
		if (uncompress(dst, &dst_len, comp, comp_len) != Z_OK ||
		    dst_len != sizeof(src) || memcmp(src, dst, sizeof(src))) {
			fprintf(stderr, "uncompress failed at level %d\n", level);
			return 1;
		}
	}

	/* Corrupted data must be detected */
	comp[comp_len / 2] ^= 0xff;
	dst_len = sizeof(dst);
	if (uncompress(dst, &dst_len, comp, comp_len) == Z_OK) {
		fprintf(stderr, "corruption not detected\n");
		return 1;
	}

	printf("selftest OK\n");
	return 0;
}

static int do_gzwrite(const char *path)
{
	char buf[BUF_SIZE];
	size_t n;
	gzFile f = gzopen(path, "wb9");

	if (!f)
		return 1;
	while ((n = fread(buf, 1, sizeof(buf), stdin)) > 0) {
		if (gzwrite(f, buf, n) != (int)n) {
			gzclose(f);
			return 1;
		}
	}
	return gzclose(f) != Z_OK;
}

static int do_gzread(const char *path)
{
	char buf[BUF_SIZE];
	int n;
	gzFile f = gzopen(path, "rb");

	if (!f)
		return 1;
	while ((n = gzread(f, buf, sizeof(buf))) > 0)
		fwrite(buf, 1, n, stdout);
	if (n < 0) {
		gzclose(f);
		return 1;
	}
	return gzclose(f) != Z_OK;
}

int main(int argc, char *argv[])
{
	if (argc == 2 && !strcmp(argv[1], "version")) {
		printf("%s\n", zlibVersion());
		return 0;
	}
	if (argc == 2 && !strcmp(argv[1], "selftest"))
		return selftest();
	if (argc == 3 && !strcmp(argv[1], "gzwrite"))
		return do_gzwrite(argv[2]);
	if (argc == 3 && !strcmp(argv[1], "gzread"))
		return do_gzread(argv[2]);

	fprintf(stderr, "Usage: %s version|selftest|gzwrite <file>|gzread <file>\n",
		argv[0]);
	return 1;
}
