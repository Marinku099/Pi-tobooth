#ifndef _XOPEN_SOURCE
#define _XOPEN_SOURCE 700
#endif

#include "fs_manager.h"

#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/statvfs.h>
#include <unistd.h>

#define FS_CLEANUP_LIST_MAX 2048

static char g_base_directory[FS_MAX_PATH_LEN] = {0};
static unsigned long g_raw_filename_counter = 0;

static void log_errno(const char *context)
{
    fprintf(stderr, "[fs_manager] %s: %s\n", context, strerror(errno));
}

static const char *subdir_for_type(image_type_t type)
{
    return (type == IMAGE_TYPE_RAW) ? FS_SUBDIR_RAW : FS_SUBDIR_FILTERED;
}

static int is_dot_entry(const char *name)
{
    return strcmp(name, ".") == 0 || strcmp(name, "..") == 0;
}

static int join_path(char *out, size_t out_len,
                     const char *base,
                     const char *subdir,
                     const char *filename)
{
    int written;

    if (subdir != NULL && filename != NULL) {
        written = snprintf(out, out_len, "%s/%s/%s", base, subdir, filename);
    } else if (subdir != NULL) {
        written = snprintf(out, out_len, "%s/%s", base, subdir);
    } else if (filename != NULL) {
        written = snprintf(out, out_len, "%s/%s", base, filename);
    } else {
        written = snprintf(out, out_len, "%s", base);
    }

    if (written < 0 || (size_t)written >= out_len) {
        fprintf(stderr, "join_path: path too long for buffer\n");
        return -1;
    }
    return 0;
}

static int build_image_path(char *out, size_t out_len,
                            image_type_t type, const char *filename)
{
    return join_path(out, out_len, g_base_directory,
                     subdir_for_type(type), filename);
}

static int ensure_directory_exists(const char *path)
{
    if (mkdir(path, 0755) == 0 || errno == EEXIST) {
        return 0;
    }
    log_errno("ensure_directory_exists: mkdir failed");
    return -1;
}

static int write_all(int fd, const unsigned char *data, size_t size)
{
    size_t total_written = 0;

    while (total_written < size) {
        ssize_t n = write(fd, data + total_written, size - total_written);

        if (n < 0) {
            if (errno == EINTR) {
                continue;
            }
            log_errno("write_all: write failed");
            return -1;
        }
        total_written += (size_t)n;
    }
    return 0;
}

static int read_all(int fd, unsigned char *buffer, size_t expected_size)
{
    size_t total_read = 0;

    while (total_read < expected_size) {
        ssize_t n = read(fd, buffer + total_read, expected_size - total_read);

        if (n < 0) {
            if (errno == EINTR) {
                continue;
            }
            log_errno("read_all: read failed");
            return -1;
        }
        if (n == 0) {
            fprintf(stderr, "read_all: unexpected EOF\n");
            return -1;
        }
        total_read += (size_t)n;
    }
    return 0;
}

static int parse_raw_sequence(const char *filename,
                              long *out_epoch,
                              unsigned long *out_counter)
{
    return sscanf(filename, "raw_%ld_%lu", out_epoch, out_counter) == 2;
}

static int compare_metadata_by_time(const void *a, const void *b)
{
    const image_metadata_t *meta_a = (const image_metadata_t *)a;
    const image_metadata_t *meta_b = (const image_metadata_t *)b;
    long epoch_a, epoch_b;
    unsigned long counter_a, counter_b;

    if (meta_a->created_at != meta_b->created_at) {
        return (meta_a->created_at < meta_b->created_at) ? -1 : 1;
    }

    if (parse_raw_sequence(meta_a->filename, &epoch_a, &counter_a) &&
        parse_raw_sequence(meta_b->filename, &epoch_b, &counter_b)) {
        if (epoch_a != epoch_b) {
            return (epoch_a < epoch_b) ? -1 : 1;
        }
        if (counter_a != counter_b) {
            return (counter_a < counter_b) ? -1 : 1;
        }
    }
    return strcmp(meta_a->filename, meta_b->filename);
}

int fs_init(const char *base_directory)
{
    static const char *const subdirs[] = {
        FS_SUBDIR_RAW, FS_SUBDIR_FILTERED, FS_SUBDIR_TMP
    };
    char path_buf[FS_MAX_PATH_LEN];
    size_t i;

    if (base_directory == NULL) {
        fprintf(stderr, "fs_init: base_directory is NULL\n");
        return -1;
    }

    if (snprintf(g_base_directory, sizeof(g_base_directory), "%s", base_directory)
        >= (int)sizeof(g_base_directory)) {
        fprintf(stderr, "fs_init: base_directory path too long\n");
        return -1;
    }

    if (ensure_directory_exists(g_base_directory) != 0) {
        return -1;
    }

    for (i = 0; i < sizeof(subdirs) / sizeof(subdirs[0]); i++) {
        if (join_path(path_buf, sizeof(path_buf),
                      g_base_directory, subdirs[i], NULL) != 0 ||
            ensure_directory_exists(path_buf) != 0) {
            return -1;
        }
    }
    return 0;
}

int fs_save_raw_image(const unsigned char *data, size_t size, char *out_filename)
{
    char unique_name[FS_MAX_FILENAME_LEN];
    char tmp_path[FS_MAX_PATH_LEN];
    char final_path[FS_MAX_PATH_LEN];
    int fd;

    if (data == NULL || size == 0 || out_filename == NULL) {
        fprintf(stderr, "fs_save_raw_image: invalid arguments\n");
        return -1;
    }

    snprintf(unique_name, sizeof(unique_name), "raw_%ld_%lu%s",
             (long)time(NULL), g_raw_filename_counter++, FS_RAW_FILE_EXTENSION);

    if (join_path(tmp_path, sizeof(tmp_path),
                  g_base_directory, FS_SUBDIR_TMP, unique_name) != 0 ||
        build_image_path(final_path, sizeof(final_path),
                         IMAGE_TYPE_RAW, unique_name) != 0) {
        return -1;
    }

    fd = open(tmp_path, O_WRONLY | O_CREAT | O_EXCL, 0644);
    if (fd < 0) {
        log_errno("fs_save_raw_image: open tmp failed");
        return -1;
    }

    if (write_all(fd, data, size) != 0) {
        close(fd);
        unlink(tmp_path);
        return -1;
    }

    if (close(fd) != 0) {
        log_errno("fs_save_raw_image: close failed");
        unlink(tmp_path);
        return -1;
    }

    if (rename(tmp_path, final_path) != 0) {
        log_errno("fs_save_raw_image: rename failed");
        unlink(tmp_path);
        return -1;
    }

    snprintf(out_filename, FS_MAX_FILENAME_LEN, "%s", unique_name);
    return 0;
}

int fs_filtered_exists(const char *filename)
{
    char path_buf[FS_MAX_PATH_LEN];
    struct stat st;

    if (filename == NULL ||
        build_image_path(path_buf, sizeof(path_buf),
                         IMAGE_TYPE_FILTERED, filename) != 0) {
        return -1;
    }

    if (stat(path_buf, &st) == 0) {
        return 1;
    }
    if (errno == ENOENT) {
        return 0;
    }
    log_errno("fs_filtered_exists: stat failed");
    return -1;
}

static int has_jpeg_header(int fd)
{
    unsigned char head[2];

    return pread(fd, head, 2, 0) == 2 && head[0] == 0xFF && head[1] == 0xD8;
}

static int has_jpeg_trailer(int fd, off_t file_size)
{
    unsigned char tail[2];

    return pread(fd, tail, 2, file_size - 2) == 2 &&
           tail[0] == 0xFF && tail[1] == 0xD9;
}

static int is_settled(const struct stat *st)
{
    struct timespec now;
    long long age_ms;

    if (clock_gettime(CLOCK_REALTIME, &now) != 0) {
        return -1;
    }
    age_ms = ((long long)now.tv_sec - (long long)st->st_mtim.tv_sec) * 1000LL +
             ((long long)now.tv_nsec - (long long)st->st_mtim.tv_nsec) / 1000000LL;
    return age_ms >= FS_FILE_SETTLE_MS;
}

int fs_filtered_is_ready(const char *filename)
{
    char path_buf[FS_MAX_PATH_LEN];
    struct stat st;
    int is_jpeg;
    int is_complete;
    int fd;

    if (filename == NULL ||
        build_image_path(path_buf, sizeof(path_buf),
                         IMAGE_TYPE_FILTERED, filename) != 0) {
        return -1;
    }

    fd = open(path_buf, O_RDONLY);
    if (fd < 0) {
        if (errno == ENOENT) {
            return 0;
        }
        log_errno("fs_filtered_is_ready: open failed");
        return -1;
    }

    if (fstat(fd, &st) != 0) {
        log_errno("fs_filtered_is_ready: fstat failed");
        close(fd);
        return -1;
    }
    if (st.st_size < 4) {
        close(fd);
        return 0;
    }

    is_jpeg = has_jpeg_header(fd);
    is_complete = is_jpeg && has_jpeg_trailer(fd, st.st_size);
    close(fd);

    if (is_jpeg) {
        return is_complete;
    }
    return is_settled(&st);
}

int fs_load_filtered_image(const char *filename,
                           unsigned char **out_data,
                           size_t *out_size)
{
    char path_buf[FS_MAX_PATH_LEN];
    struct stat st;
    unsigned char *buffer;
    int fd;

    if (filename == NULL || out_data == NULL || out_size == NULL) {
        fprintf(stderr, "fs_load_filtered_image: invalid arguments\n");
        return -1;
    }
    if (build_image_path(path_buf, sizeof(path_buf),
                         IMAGE_TYPE_FILTERED, filename) != 0) {
        return -1;
    }

    fd = open(path_buf, O_RDONLY);
    if (fd < 0) {
        log_errno("fs_load_filtered_image: open failed");
        return -1;
    }

    if (fstat(fd, &st) != 0) {
        log_errno("fs_load_filtered_image: fstat failed");
        close(fd);
        return -1;
    }

    buffer = (unsigned char *)malloc((size_t)st.st_size);
    if (buffer == NULL) {
        fprintf(stderr, "fs_load_filtered_image: malloc failed for %ld bytes\n",
                (long)st.st_size);
        close(fd);
        return -1;
    }

    if (read_all(fd, buffer, (size_t)st.st_size) != 0) {
        free(buffer);
        close(fd);
        return -1;
    }
    close(fd);

    *out_data = buffer;
    *out_size = (size_t)st.st_size;
    return 0;
}

int fs_list_images(image_type_t type, image_metadata_t *out_list, int max_items)
{
    char dir_path[FS_MAX_PATH_LEN];
    char entry_path[FS_MAX_PATH_LEN];
    DIR *dir;
    struct dirent *entry;
    struct stat st;
    int count = 0;

    if (out_list == NULL || max_items <= 0) {
        fprintf(stderr, "fs_list_images: invalid arguments\n");
        return -1;
    }
    if (build_image_path(dir_path, sizeof(dir_path), type, NULL) != 0) {
        return -1;
    }

    dir = opendir(dir_path);
    if (dir == NULL) {
        log_errno("fs_list_images: opendir failed");
        return -1;
    }

    while ((entry = readdir(dir)) != NULL && count < max_items) {
        if (is_dot_entry(entry->d_name)) {
            continue;
        }
        if (join_path(entry_path, sizeof(entry_path),
                      dir_path, NULL, entry->d_name) != 0) {
            continue;
        }
        if (stat(entry_path, &st) != 0) {
            log_errno("fs_list_images: stat failed, skipping entry");
            continue;
        }
        if (!S_ISREG(st.st_mode)) {
            continue;
        }

        snprintf(out_list[count].filename, FS_MAX_FILENAME_LEN, "%s", entry->d_name);
        out_list[count].created_at = st.st_mtime;
        out_list[count].file_size_bytes = (size_t)st.st_size;
        out_list[count].type = type;
        count++;
    }
    closedir(dir);

    qsort(out_list, (size_t)count, sizeof(image_metadata_t), compare_metadata_by_time);
    return count;
}

static int unlink_if_exists(const char *path, const char *error_context)
{
    if (unlink(path) != 0 && errno != ENOENT) {
        log_errno(error_context);
        return -1;
    }
    return 0;
}

int fs_delete_pair(const char *filename)
{
    char raw_path[FS_MAX_PATH_LEN];
    char filtered_path[FS_MAX_PATH_LEN];
    int had_error = 0;

    if (filename == NULL ||
        build_image_path(raw_path, sizeof(raw_path),
                         IMAGE_TYPE_RAW, filename) != 0 ||
        build_image_path(filtered_path, sizeof(filtered_path),
                         IMAGE_TYPE_FILTERED, filename) != 0) {
        return -1;
    }

    if (unlink_if_exists(raw_path, "fs_delete_pair: unlink raw failed") != 0) {
        had_error = 1;
    }
    if (unlink_if_exists(filtered_path, "fs_delete_pair: unlink filtered failed") != 0) {
        had_error = 1;
    }
    return had_error ? -1 : 0;
}

double fs_get_disk_free_percent(const char *path)
{
    struct statvfs vfs;

    if (path == NULL) {
        return -1.0;
    }
    if (statvfs(path, &vfs) != 0) {
        log_errno("fs_get_disk_free_percent: statvfs failed");
        return -1.0;
    }
    if (vfs.f_blocks == 0) {
        return -1.0;
    }
    return 100.0 * (double)vfs.f_bavail / (double)vfs.f_blocks;
}

static int sum_directory_bytes(const char *dir_path, long long *out_total_bytes)
{
    char entry_path[FS_MAX_PATH_LEN];
    struct dirent *entry;
    struct stat st;
    long long total_bytes = 0;
    DIR *dir = opendir(dir_path);

    if (dir == NULL) {
        log_errno("sum_directory_bytes: opendir failed");
        return -1;
    }

    while ((entry = readdir(dir)) != NULL) {
        if (is_dot_entry(entry->d_name)) {
            continue;
        }
        if (join_path(entry_path, sizeof(entry_path),
                      dir_path, NULL, entry->d_name) != 0) {
            continue;
        }
        if (stat(entry_path, &st) != 0 || !S_ISREG(st.st_mode)) {
            continue;
        }
        total_bytes += (long long)st.st_size;
    }
    closedir(dir);

    *out_total_bytes = total_bytes;
    return 0;
}

long long fs_get_media_usage_bytes(void)
{
    static const image_type_t types[] = { IMAGE_TYPE_RAW, IMAGE_TYPE_FILTERED };
    char dir_path[FS_MAX_PATH_LEN];
    long long total_bytes = 0;
    size_t i;

    if (g_base_directory[0] == '\0') {
        fprintf(stderr,
                "[fs_manager] fs_get_media_usage_bytes: fs_init() has not been called\n");
        return -1;
    }

    for (i = 0; i < sizeof(types) / sizeof(types[0]); i++) {
        long long dir_bytes = 0;

        if (build_image_path(dir_path, sizeof(dir_path), types[i], NULL) != 0 ||
            sum_directory_bytes(dir_path, &dir_bytes) != 0) {
            return -1;
        }
        total_bytes += dir_bytes;
    }
    return total_bytes;
}

static long long filtered_file_size_bytes(const char *filename)
{
    char path_buf[FS_MAX_PATH_LEN];
    struct stat st;

    if (build_image_path(path_buf, sizeof(path_buf),
                         IMAGE_TYPE_FILTERED, filename) != 0 ||
        stat(path_buf, &st) != 0) {
        return 0;
    }
    return (long long)st.st_size;
}

static int delete_oldest_safe_pair(const image_metadata_t *raw_list,
                                   int candidate_count,
                                   long long *media_usage_bytes)
{
    int i;

    for (i = 0; i < candidate_count; i++) {
        const char *name = raw_list[i].filename;
        long long pair_bytes;

        if (fs_filtered_is_ready(name) <= 0) {
            continue;
        }

        pair_bytes = (long long)raw_list[i].file_size_bytes
                     + filtered_file_size_bytes(name);

        if (fs_delete_pair(name) != 0) {
            return 0;
        }

        *media_usage_bytes -= pair_bytes;
        if (*media_usage_bytes < 0) {
            *media_usage_bytes = 0;
        }
        return 1;
    }
    return 0;
}

int fs_cleanup_old_files(const char *base_directory,
                         double threshold_percent,
                         long long max_media_bytes)
{
    image_metadata_t *raw_list;
    const int quota_enabled = (max_media_bytes > 0);
    int safety_iterations = FS_CLEANUP_LIST_MAX;
    int total_deleted = 0;
    long long media_usage_bytes = 0;

    if (base_directory == NULL) {
        return -1;
    }

    if (quota_enabled) {
        media_usage_bytes = fs_get_media_usage_bytes();
        if (media_usage_bytes < 0) {
            return -1;
        }
    }

    raw_list = (image_metadata_t *)malloc(sizeof(image_metadata_t) * FS_CLEANUP_LIST_MAX);
    if (raw_list == NULL) {
        fprintf(stderr, "fs_cleanup_old_files: malloc failed\n");
        return -1;
    }

    while (safety_iterations-- > 0) {
        double free_percent = fs_get_disk_free_percent(base_directory);
        int raw_count;
        int candidate_count;

        if (free_percent < 0.0) {
            total_deleted = -1;
            break;
        }

        if (free_percent >= threshold_percent &&
            !(quota_enabled && media_usage_bytes > max_media_bytes)) {
            break;
        }

        raw_count = fs_list_images(IMAGE_TYPE_RAW, raw_list, FS_CLEANUP_LIST_MAX);
        if (raw_count < 0) {
            total_deleted = -1;
            break;
        }

        candidate_count = raw_count - FS_PROTECT_RECENT_COUNT;
        if (candidate_count <= 0) {
            break;
        }

        if (!delete_oldest_safe_pair(raw_list, candidate_count, &media_usage_bytes)) {
            break;
        }
        total_deleted++;
    }

    free(raw_list);
    return total_deleted;
}

static void remove_cache_entry(image_cache_t *cache, int index)
{
    free(cache->entries[index].image_data);
    cache->current_size_bytes -= cache->entries[index].data_size;

    memmove(&cache->entries[index], &cache->entries[index + 1],
            sizeof(cache_entry_t) * (size_t)(cache->count - index - 1));
    cache->count--;
}

static int find_cache_entry(const image_cache_t *cache, const char *filename)
{
    int i;

    for (i = 0; i < cache->count; i++) {
        if (strcmp(cache->entries[i].filename, filename) == 0) {
            return i;
        }
    }
    return -1;
}

static void append_cache_entry(image_cache_t *cache, const char *filename,
                               unsigned char *data, size_t size)
{
    cache_entry_t *slot = &cache->entries[cache->count];

    snprintf(slot->filename, FS_MAX_FILENAME_LEN, "%s", filename);
    slot->image_data = data;
    slot->data_size = size;
    slot->loaded_at = time(NULL);

    cache->count++;
    cache->current_size_bytes += size;
}

int cache_init(image_cache_t *cache, size_t max_size_bytes)
{
    if (cache == NULL) {
        return -1;
    }
    memset(cache, 0, sizeof(image_cache_t));
    cache->max_size_bytes = max_size_bytes;
    return 0;
}

int cache_get_filtered(image_cache_t *cache, const char *filename,
                       unsigned char **out_data, size_t *out_size)
{
    unsigned char *loaded_data;
    size_t loaded_size;
    int index;
    int ready;

    if (cache == NULL || filename == NULL || out_data == NULL || out_size == NULL) {
        return -1;
    }

    index = find_cache_entry(cache, filename);
    if (index >= 0) {
        *out_data = cache->entries[index].image_data;
        *out_size = cache->entries[index].data_size;
        return 0;
    }

    ready = fs_filtered_is_ready(filename);
    if (ready < 0) {
        return -1;
    }
    if (ready == 0) {
        return FS_ERR_NOT_READY;
    }

    if (fs_load_filtered_image(filename, &loaded_data, &loaded_size) != 0) {
        return -1;
    }

    while (cache->count >= FS_MAX_CACHE_ITEMS ||
           cache->current_size_bytes + loaded_size > cache->max_size_bytes) {
        if (cache->count == 0) {
            fprintf(stderr,
                    "cache_get_filtered: item larger than whole cache, bypassing cache\n");
            *out_data = loaded_data;
            *out_size = loaded_size;
            return 0;
        }
        remove_cache_entry(cache, 0);
    }

    append_cache_entry(cache, filename, loaded_data, loaded_size);

    *out_data = loaded_data;
    *out_size = loaded_size;
    return 0;
}

void cache_invalidate(image_cache_t *cache, const char *filename)
{
    int index;

    if (cache == NULL || filename == NULL) {
        return;
    }

    index = find_cache_entry(cache, filename);
    if (index >= 0) {
        remove_cache_entry(cache, index);
    }
}

void cache_destroy(image_cache_t *cache)
{
    int i;

    if (cache == NULL) {
        return;
    }

    for (i = 0; i < cache->count; i++) {
        free(cache->entries[i].image_data);
    }
    cache->count = 0;
    cache->current_size_bytes = 0;
}
