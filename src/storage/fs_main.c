#include "fs_manager.h"
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/inotify.h>
#include <limits.h>
#include <errno.h>

int main()
{
    const char *dir = getenv("PHOTOBOOTH_DIR");
    char raw_path[PATH_MAX];
    char filtered_path[PATH_MAX];

    snprintf(raw_path, sizeof raw_path, "%s/%s", dir, FS_SUBDIR_RAW);
    snprintf(filtered_path, sizeof filtered_path, "%s/%s", dir, FS_SUBDIR_FILTERED);

    setvbuf(stdout, NULL, _IOLBF, 0);

    printf("start fs_main\n");

    int init = fs_init(getenv("PHOTOBOOTH_DIR"));
    if (init == 0)
    {
        printf("init succesfully\n");
    }

    int fd;
    int wd[2];
    fd = inotify_init();

    if (fd < 0)
    {
        perror("Couldn't init inotify");
        return 1;
    }

    wd[0] = inotify_add_watch(fd, raw_path, IN_CREATE | IN_CLOSE_WRITE | IN_DELETE);
    if (wd[0] == -1)
    {
        printf("Couldn't add watch to %s\n", raw_path);
        return 1;
    }
    else
    {
        printf("Watching:: %s\n", raw_path);
    }

    wd[1] = inotify_add_watch(fd, filtered_path, IN_CREATE | IN_CLOSE_WRITE | IN_DELETE);

    if (wd[1] == -1)
    {
        printf("Couldn't add watch to %s\n", filtered_path);
        return 1;
    }
    else
    {
        printf("Watching:: %s\n", filtered_path);
    }

    char buf[4096]
        __attribute__((aligned(__alignof__(struct inotify_event))));
    const struct inotify_event *event;
    ssize_t size;
    double remaining_space;
    for (;;)
    {
        size = read(fd, buf, sizeof(buf));

        if (size == -1)
        {
            if (errno == EINTR)
                continue;
            perror("read");
            return 1;
        }

        for (char *ptr = buf; ptr < buf + size; ptr += sizeof(struct inotify_event) + event->len)
        {
            event = (const struct inotify_event *)ptr;

            if (event->mask & IN_CREATE){
                printf("IN_CREATE\n");
                remaining_space = fs_get_disk_free_percent(dir);
                printf("remaining space: %.2f percent\n",remaining_space);
                if(remaining_space < FS_DISK_FREE_THRESHOLD_PERCENT){
                    printf("insufficient space, cleaning...\n");
                    fs_cleanup_old_files(dir, FS_DEFAULT_MEDIA_QUOTA_BYTES);
                    remaining_space = fs_get_disk_free_percent(dir);
                    printf("remaining space: %.2lf\n",remaining_space);
                }
            }
            if (event->mask & IN_CLOSE_WRITE)
                printf("IN_CLOSE_WRITE\n");
            if (event->mask & IN_DELETE)
                printf("IN_DELETE\n");

            /* Print the name of the watched directory.  */
            for (size_t i = 0; i < 2; i++)
            {
                if (wd[i] == event->wd)
                {
                    printf("DIR %zu\n", i);
                    break;
                }
            }

            /* Print the name of the file.  */
            if (event->len)
                printf("%s\n", event->name);
        }
    }

    return 0;
}