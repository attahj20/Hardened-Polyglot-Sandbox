
#include <stdio.h>
#include <unistd.h>

int main() {
    printf("[+] Sandbox execution started...\n");

    // Attempting to read a sensitive host file
    FILE *file = fopen("/etc/shadow", "r");
    if (file == NULL) {
        perror("[-] Access denied (Expected sandbox behavior)");
    } else {
        printf("[!] Exploit Success! Read host system file.\n");
        fclose(file);
    }
    return 0;
}
