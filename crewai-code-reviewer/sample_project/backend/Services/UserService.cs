using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Threading.Tasks;

namespace SampleApi.Services
{
    // Issue: No interface defined (violates DI and testability)
    // Issue: Class does too many things (violates SRP)
    public class UserService
    {
        // Issue: Creating HttpClient directly instead of using IHttpClientFactory
        private readonly HttpClient _httpClient = new HttpClient();

        // Issue: Mutable static state - not thread-safe
        private static List<string> _cache = new List<string>();

        // Issue: Synchronous method doing I/O
        public string GetExternalUserData(string userId)
        {
            // Issue: .Result blocks the thread (sync-over-async)
            var response = _httpClient.GetAsync($"https://api.example.com/users/{userId}").Result;
            var content = response.Content.ReadAsStringAsync().Result;

            // Issue: No error handling for HTTP failures
            // Issue: No response status code check

            return content;
        }

        // Issue: Method does not propagate CancellationToken
        public async Task<List<string>> GetAllUsersAsync()
        {
            var users = new List<string>();

            // Issue: N+1 problem - fetching details one by one
            var ids = await GetUserIdsAsync();
            foreach (var id in ids)
            {
                var user = await GetUserByIdAsync(id);
                users.Add(user);
            }

            return users;
        }

        private async Task<List<string>> GetUserIdsAsync()
        {
            // Issue: No caching of this frequently-called data
            var response = await _httpClient.GetAsync("https://api.example.com/users/ids");
            var content = await response.Content.ReadAsStringAsync();
            return System.Text.Json.JsonSerializer.Deserialize<List<string>>(content);
        }

        private async Task<string> GetUserByIdAsync(string id)
        {
            var response = await _httpClient.GetAsync($"https://api.example.com/users/{id}");
            return await response.Content.ReadAsStringAsync();
        }

        // Issue: This method catches all exceptions silently
        public void ProcessUserData(string data)
        {
            try
            {
                // Business logic here...
                var processed = data.ToUpper(); // Placeholder

                // Issue: String concatenation in loop for logging
                string logMessage = "";
                for (int i = 0; i < 1000; i++)
                {
                    logMessage += $"Processing item {i}\n";
                }
                Console.WriteLine(logMessage); // Issue: Using Console instead of ILogger
            }
            catch (Exception ex)
            {
                // Issue: Swallowing exceptions
                // Issue: No logging of the exception
            }
        }

        // Issue: Disposing HttpClient in a method - should be managed by DI
        public void Cleanup()
        {
            _httpClient.Dispose();
        }
    }
}
