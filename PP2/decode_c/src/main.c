// try #1
#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <unistd.h>
#include <signal.h>
#include <sys/time.h>
#include <string.h>
#include <stdint.h>

#define WEIGHT 100
#define HEIGHT 100
#define TOTAL_PIXELS (WEIGHT * HEIGHT)

volatile int time_ms = 0;
int tests[] = {88, 222, 5, 934};
volatile int progress[4] = {0, 0, 0, 0};
pthread_t threads[4];
pthread_mutex_t progress_mutex = PTHREAD_MUTEX_INITIALIZER;

void* Decode(void* arg) {
    int thread_index = *(int*)arg;
    int key = tests[thread_index];
    printf("Thread %d starting with key %d\n", thread_index, key);
    FILE* encrypted_file = fopen("encrypt.bin", "rb");
    if (encrypted_file == NULL) {
        printf("Error: Cannot open encrypt.bin\n");
        free(arg);
        return NULL;
    }
    system("mkdir -p outputs");
    char ppm_filename[50];
    char txt_filename[50];
    snprintf(ppm_filename, sizeof(ppm_filename), "outputs/output_%d.ppm", key);
    snprintf(txt_filename, sizeof(txt_filename), "outputs/output_%d.txt", key);
    FILE* ppm_file = fopen(ppm_filename, "wb");
    FILE* txt_file = fopen(txt_filename, "w");
    if (ppm_file == NULL || txt_file == NULL) {
        printf("Error: Cannot create output files for key %d\n", key);
        fclose(encrypted_file);
        free(arg);
        return NULL;
    }
    // write PPM header
    fprintf(ppm_file, "P6\n%d %d\n255\n", WEIGHT, HEIGHT);
    unsigned char pixel[3];
    for (int i = 0; i < TOTAL_PIXELS; i++) {
        if (fread(pixel, sizeof(unsigned char), 3, encrypted_file) != 3) {
            break;
        }
        unsigned char key_byte = key & 0xFF;
        unsigned char r = pixel[0] ^ key_byte;
        unsigned char g = pixel[1] ^ key_byte;
        unsigned char b = pixel[2] ^ key_byte;
        // write to PPM file
        fwrite(&r, sizeof(unsigned char), 1, ppm_file);
        fwrite(&g, sizeof(unsigned char), 1, ppm_file);
        fwrite(&b, sizeof(unsigned char), 1, ppm_file);
        // write to TXT file
        fprintf(txt_file, "%d %d %d\n", r, g, b);
        pthread_mutex_lock(&progress_mutex);
        progress[thread_index]++;
        pthread_mutex_unlock(&progress_mutex);
        // wait 200 microseconds
        usleep(200);
    }
    fclose(encrypted_file);
    fclose(ppm_file);
    fclose(txt_file);
    free(arg);
    printf("Thread %d (key %d) finished\n", thread_index, key);
    return NULL;
}

void TimerHandler(int signum) {
    if (signum != SIGALRM) return;
    pthread_mutex_lock(&progress_mutex);
    printf("Timer tick: %d ms\n", time_ms);
    for (int i = 0; i < 4; i++) {
        double percentage = (progress[i] * 100.0) / TOTAL_PIXELS;
        printf("  Thread %d (key %d): %d/%d pixels (%.2f%%)\n", i, tests[i], progress[i], TOTAL_PIXELS, percentage);
    }
    printf("\n");
    time_ms += 200;
    pthread_mutex_unlock(&progress_mutex);
}

int main() {
    struct sigaction sa;
    struct itimerval timer;
    printf("Starting decoder with 4 threads...\n");
    // Set up signal handler
    sa.sa_handler = TimerHandler;
    sa.sa_flags = 0;
    sigemptyset(&sa.sa_mask);
    if (sigaction(SIGALRM, &sa, NULL) == -1) {
        perror("sigaction");
        return 1;
    }
    timer.it_value.tv_sec = 0;
    timer.it_value.tv_usec = 100000;  // 100ms
    timer.it_interval.tv_sec = 0;
    timer.it_interval.tv_usec = 200000;  // 200ms
    if (setitimer(ITIMER_REAL, &timer, NULL) == -1) {
        perror("setitimer");
        return 1;
    }
    for (int i = 0; i < 4; i++) {
        int* thread_index = malloc(sizeof(int));
        *thread_index = i;
        if (pthread_create(&threads[i], NULL, Decode, thread_index) != 0) {
            printf("Error creating thread %d\n", i);
            free(thread_index);
        }
    }
    for (int i = 0; i < 4; i++) {
        pthread_join(threads[i], NULL);
    }
    timer.it_value.tv_sec = 0;
    timer.it_value.tv_usec = 0;
    timer.it_interval.tv_sec = 0;
    timer.it_interval.tv_usec = 0;
    setitimer(ITIMER_REAL, &timer, NULL);
    printf("\nFinal results:\n");
    for (int i = 0; i < 4; i++) {
        double percentage = (progress[i] * 100.0) / TOTAL_PIXELS;
        printf("  Thread %d (key %d): %d/%d pixels (%.2f%%)\n", i, tests[i], progress[i], TOTAL_PIXELS, percentage);
    }
    printf("\nAll threads completed.\n");
    pthread_mutex_destroy(&progress_mutex);
    return 0;
}