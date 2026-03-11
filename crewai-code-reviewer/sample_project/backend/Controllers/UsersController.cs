using Microsoft.AspNetCore.Mvc;
using Microsoft.Data.SqlClient;
using System.Data;

namespace SampleApi.Controllers
{
    // Issue: No [ApiController] attribute
    // Issue: No route versioning
    [Route("api/[controller]")]
    public class UsersController : ControllerBase
    {
        // Issue: Direct SqlConnection instead of using EF Core or repository pattern
        private readonly string _connectionString = "Server=localhost;Database=MyDb;User=sa;Password=P@ssw0rd123;";
        // Issue: Hardcoded connection string with credentials

        // Issue: No ILogger injection
        // Issue: No service layer - business logic in controller

        // Issue: No async suffix, not properly async
        [HttpGet]
        public IActionResult GetUsers()
        {
            // Issue: Synchronous database call
            var users = new List<object>();

            using (var connection = new SqlConnection(_connectionString))
            {
                connection.Open();

                // Issue: SQL Injection vulnerability!
                var searchTerm = HttpContext.Request.Query["search"].ToString();
                var query = $"SELECT * FROM Users WHERE Name LIKE '%{searchTerm}%'";

                using (var command = new SqlCommand(query, connection))
                {
                    using (var reader = command.ExecuteReader())
                    {
                        while (reader.Read())
                        {
                            // Issue: Exposing all fields including sensitive data
                            users.Add(new
                            {
                                Id = reader["Id"],
                                Name = reader["Name"],
                                Email = reader["Email"],
                                PasswordHash = reader["PasswordHash"],  // Issue: Exposing password hash!
                                SSN = reader["SSN"],                    // Issue: Exposing PII
                                Salary = reader["Salary"],
                            });
                        }
                    }
                }
            }

            return Ok(users);
        }

        [HttpGet("{id}")]
        public IActionResult GetUser(int id)
        {
            // Issue: No input validation
            // Issue: No null check / 404 handling
            using (var connection = new SqlConnection(_connectionString))
            {
                connection.Open();
                var command = new SqlCommand($"SELECT * FROM Users WHERE Id = {id}", connection);
                var reader = command.ExecuteReader();
                reader.Read();

                return Ok(new
                {
                    Id = reader["Id"],
                    Name = reader["Name"],
                    Email = reader["Email"],
                });
            }
            // Issue: reader and command not properly disposed
        }

        [HttpPost]
        public IActionResult CreateUser([FromBody] dynamic user)
        {
            // Issue: Using dynamic instead of a typed DTO
            // Issue: No model validation
            // Issue: No [Authorize] attribute
            // Issue: No CSRF protection

            using (var connection = new SqlConnection(_connectionString))
            {
                connection.Open();

                // Issue: SQL Injection via string interpolation
                var query = $"INSERT INTO Users (Name, Email) VALUES ('{user.Name}', '{user.Email}')";
                var command = new SqlCommand(query, connection);
                command.ExecuteNonQuery();
            }

            // Issue: Not returning 201 Created with location header
            return Ok(new { message = "User created" });
        }

        [HttpDelete("{id}")]
        // Issue: No authorization check - anyone can delete users!
        public IActionResult DeleteUser(int id)
        {
            // Issue: No soft delete, permanent deletion
            // Issue: No audit logging
            using (var connection = new SqlConnection(_connectionString))
            {
                connection.Open();
                var command = new SqlCommand($"DELETE FROM Users WHERE Id = {id}", connection);
                command.ExecuteNonQuery();
            }

            return Ok();
        }
    }
}
