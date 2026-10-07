#ifndef FS_MANAGER_H
#define FS_MANAGER_H

#include <stddef.h>
#include <time.h>

#define FS_MAX_FILENAME_LEN             256
#define FS_MAX_PATH_LEN                 512

#define FS_SUBDIR_RAW                   "raw_images"
#define FS_SUBDIR_FILTERED              "filtered_images"
#define FS_SUBDIR_TMP                   "tmp"

#define FS_RAW_FILE_EXTENSION           ".jpg"

#define FS_MAX_CACHE_ITEMS              16
#define FS_MAX_CACHE_BYTES              (64 * 1024 * 1024)

#define FS_DISK_FREE_THRESHOLD_PERCENT  10.0
#define FS_DEFAULT_MEDIA_QUOTA_BYTES    (1024LL * 1024LL * 1024LL)
#define FS_PROTECT_RECENT_COUNT         5

#define FS_ERR_NOT_READY                (-2)
#define FS_FILE_SETTLE_MS               1000

typedef enum {
    IMAGE_TYPE_RAW = 0,
    IMAGE_TYPE_FILTERED = 1
} image_type_t;

typedef struct {
    char         filename[FS_MAX_FILENAME_LEN];
    time_t       created_at;
    size_t       file_size_bytes;
    image_type_t type;
} image_metadata_t;

typedef struct {
    char           filename[FS_MAX_FILENAME_LEN];
    unsigned char *image_data;
    size_t         data_size;
    time_t         loaded_at;
} cache_entry_t;

typedef struct {
    cache_entry_t entries[FS_MAX_CACHE_ITEMS];
    int           count;
    size_t        max_size_bytes;
    size_t        current_size_bytes;
} image_cache_t;

int fs_init(const char *base_directory);

int fs_save_raw_image(const unsigned char *data,
                      size_t size,
                      char *out_filename);

int fs_filtered_exists(const char *filename);
int fs_filtered_is_ready(const char *filename);

int fs_load_filtered_image(const char *filename,
                           unsigned char **out_data,
                           size_t *out_size);

int fs_list_images(image_type_t type,
                   image_metadata_t *out_list,
                   int max_items);

int fs_delete_pair(const char *filename);

double fs_get_disk_free_percent(const char *path);
long long fs_get_media_usage_bytes(void);

int fs_cleanup_old_files(const char *base_directory,
                         double threshold_percent,
                         long long max_media_bytes);

int cache_init(image_cache_t *cache, size_t max_size_bytes);

int cache_get_filtered(image_cache_t *cache,
                       const char *filename,
                       unsigned char **out_data,
                       size_t *out_size);

void cache_invalidate(image_cache_t *cache, const char *filename);
void cache_destroy(image_cache_t *cache);

#endif
