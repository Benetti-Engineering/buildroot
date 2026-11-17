/*
 * Minimal read-only FUSE filesystem, exposing a single "hello" file.
 *
 * Usage: fuse3-hello [FUSE options] <mountpoint>
 */

#define FUSE_USE_VERSION 31

#include <errno.h>
#include <fcntl.h>
#include <fuse.h>
#include <string.h>
#include <sys/stat.h>

static const char *hello_path = "/hello";
static const char *hello_str = "Hello Buildroot FUSE\n";

static void *hello_init(struct fuse_conn_info *conn, struct fuse_config *cfg)
{
	(void)conn;
	cfg->kernel_cache = 1;
	return NULL;
}

static int hello_getattr(const char *path, struct stat *st,
			 struct fuse_file_info *fi)
{
	(void)fi;
	memset(st, 0, sizeof(*st));
	if (strcmp(path, "/") == 0) {
		st->st_mode = S_IFDIR | 0755;
		st->st_nlink = 2;
	} else if (strcmp(path, hello_path) == 0) {
		st->st_mode = S_IFREG | 0444;
		st->st_nlink = 1;
		st->st_size = strlen(hello_str);
	} else {
		return -ENOENT;
	}
	return 0;
}

static int hello_readdir(const char *path, void *buf, fuse_fill_dir_t filler,
			 off_t offset, struct fuse_file_info *fi,
			 enum fuse_readdir_flags flags)
{
	(void)offset;
	(void)fi;
	(void)flags;
	if (strcmp(path, "/") != 0)
		return -ENOENT;

	filler(buf, ".", NULL, 0, 0);
	filler(buf, "..", NULL, 0, 0);
	filler(buf, hello_path + 1, NULL, 0, 0);
	return 0;
}

static int hello_open(const char *path, struct fuse_file_info *fi)
{
	if (strcmp(path, hello_path) != 0)
		return -ENOENT;
	if ((fi->flags & O_ACCMODE) != O_RDONLY)
		return -EACCES;
	return 0;
}

static int hello_read(const char *path, char *buf, size_t size, off_t offset,
		      struct fuse_file_info *fi)
{
	size_t len = strlen(hello_str);

	(void)fi;
	if (strcmp(path, hello_path) != 0)
		return -ENOENT;
	if ((size_t)offset >= len)
		return 0;
	if (offset + size > len)
		size = len - offset;
	memcpy(buf, hello_str + offset, size);
	return size;
}

static const struct fuse_operations hello_ops = {
	.init = hello_init,
	.getattr = hello_getattr,
	.readdir = hello_readdir,
	.open = hello_open,
	.read = hello_read,
};

int main(int argc, char *argv[])
{
	return fuse_main(argc, argv, &hello_ops, NULL);
}
