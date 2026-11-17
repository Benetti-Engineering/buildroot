/*
 * Test program for the Netscape Portable Runtime (NSPR) library.
 */

#include <stdio.h>
#include <string.h>

#include <nspr.h>
#include <plstr.h>

#define NUM_THREADS 4
#define NUM_LOOPS 10000

static PRLock *lock;
static PRInt32 counter;
static PRInt32 atomic_counter;

static void worker(void *arg)
{
	int i;

	(void)arg;
	for (i = 0; i < NUM_LOOPS; i++) {
		PR_Lock(lock);
		counter++;
		PR_Unlock(lock);
		PR_ATOMIC_INCREMENT(&atomic_counter);
	}
}

static int test_threads(void)
{
	PRThread *threads[NUM_THREADS];
	int i;

	lock = PR_NewLock();
	if (!lock)
		return 1;

	for (i = 0; i < NUM_THREADS; i++) {
		threads[i] = PR_CreateThread(PR_USER_THREAD, worker, NULL,
					     PR_PRIORITY_NORMAL,
					     PR_GLOBAL_THREAD,
					     PR_JOINABLE_THREAD, 0);
		if (!threads[i])
			return 1;
	}
	for (i = 0; i < NUM_THREADS; i++)
		if (PR_JoinThread(threads[i]) != PR_SUCCESS)
			return 1;

	PR_DestroyLock(lock);

	printf("threads: counter=%d atomic=%d\n", counter, atomic_counter);
	return counter != NUM_THREADS * NUM_LOOPS ||
		atomic_counter != NUM_THREADS * NUM_LOOPS;
}

static int test_time(void)
{
	PRExplodedTime et;
	PRTime t;
	char buf[64];

	/* 2000-01-02 03:04:05 UTC */
	memset(&et, 0, sizeof(et));
	et.tm_year = 2000;
	et.tm_month = 0;
	et.tm_mday = 2;
	et.tm_hour = 3;
	et.tm_min = 4;
	et.tm_sec = 5;
	t = PR_ImplodeTime(&et);
	if (t != (PRTime)946782245 * PR_USEC_PER_SEC)
		return 1;

	PR_ExplodeTime(t, PR_GMTParameters, &et);
	PR_FormatTimeUSEnglish(buf, sizeof(buf), "%Y-%m-%d %H:%M:%S", &et);
	printf("time: %s\n", buf);
	return strcmp(buf, "2000-01-02 03:04:05");
}

static int test_strings(void)
{
	char buf[64];
	char *s;

	PR_snprintf(buf, sizeof(buf), "%s-%d-%lld", "nspr", 42,
		    (PRInt64)1 << 40);
	printf("snprintf: %s\n", buf);
	if (strcmp(buf, "nspr-42-1099511627776"))
		return 1;

	s = PL_strdup("Hello Buildroot");
	if (!s || PL_strcasecmp(s, "hello buildroot"))
		return 1;
	PL_strfree(s);

	return 0;
}

static int test_file(const char *path)
{
	static const char msg[] = "Hello NSPR file";
	char buf[64];
	PRFileDesc *fd;
	PRInt32 n;

	fd = PR_Open(path, PR_WRONLY | PR_CREATE_FILE | PR_TRUNCATE, 0644);
	if (!fd)
		return 1;
	if (PR_Write(fd, msg, sizeof(msg)) != sizeof(msg))
		return 1;
	PR_Close(fd);

	fd = PR_Open(path, PR_RDONLY, 0);
	if (!fd)
		return 1;
	n = PR_Read(fd, buf, sizeof(buf));
	PR_Close(fd);
	PR_Delete(path);

	printf("file: %s\n", buf);
	return n != sizeof(msg) || strcmp(buf, msg);
}

int main(void)
{
	int ret = 0;

	PR_Init(PR_USER_THREAD, PR_PRIORITY_NORMAL, 0);

	printf("NSPR version: %s\n", PR_GetVersion());
	if (!PR_VersionCheck(PR_VERSION)) {
		fprintf(stderr, "version check failed\n");
		return 1;
	}

	ret |= test_threads();
	ret |= test_time();
	ret |= test_strings();
	ret |= test_file("/tmp/nspr-test.txt");

	if (PR_Cleanup() != PR_SUCCESS)
		ret = 1;

	printf("NSPR test %s\n", ret ? "FAILED" : "OK");
	return ret;
}
