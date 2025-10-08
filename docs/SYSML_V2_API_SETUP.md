# SysML V2 API Services Setup Guide

This guide explains how to set up and run the SysML V2 API Services to enable actual API integration with sysml2pytest.

## Overview

The SysML V2 API Services provide a REST API for accessing and manipulating SysML V2 models. This is the official reference implementation from the OMG SysML v2 Submission Team.

## Prerequisites

- **Java 17 or later** (required for running the API server)
- **Docker** (optional, for containerized deployment)
- **Git** (to clone the repository)

## Option 1: Running with Docker (Recommended)

### Quick Start

```bash
# Pull and run the official Docker image
docker run -p 9000:9000 sysml/sysml-v2-api-server:latest
```

The API will be available at `http://localhost:9000`

### Custom Docker Setup

```bash
# Clone the SysML V2 Release repository
git clone https://github.com/Systems-Modeling/SysML-v2-Release.git
cd SysML-v2-Release/install/docker

# Build the Docker image
docker build -t sysml-v2-api-server .

# Run the container
docker run -d \
  --name sysml-v2-api \
  -p 9000:9000 \
  -v $(pwd)/data:/data \
  sysml-v2-api-server

# Check logs
docker logs -f sysml-v2-api
```

## Option 2: Running from Source

### Step 1: Clone the Repository

```bash
git clone https://github.com/Systems-Modeling/SysML-v2-Release.git
cd SysML-v2-Release
```

### Step 2: Install Java 17+

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install openjdk-17-jdk
java -version
```

**macOS (Homebrew):**
```bash
brew install openjdk@17
java -version
```

**Windows:**
Download from [AdoptOpenJDK](https://adoptopenjdk.net/) or [Oracle](https://www.oracle.com/java/technologies/downloads/)

### Step 3: Build the API Server

```bash
# Navigate to the API server directory
cd install/sysml2-jupyter-docker

# Build using Gradle
./gradlew build

# Or download pre-built release
wget https://github.com/Systems-Modeling/SysML-v2-Release/releases/download/2024-XX/sysml-v2-api-server.jar
```

### Step 4: Run the API Server

```bash
# Run with default settings
java -jar sysml-v2-api-server.jar

# Run with custom port
java -jar sysml-v2-api-server.jar --server.port=9000

# Run with custom database
java -jar sysml-v2-api-server.jar --spring.datasource.url=jdbc:postgresql://localhost:5432/sysmldb
```

The API will start on `http://localhost:9000` (or your specified port)

## Option 3: Using Eclipse Pilot Implementation

The Eclipse SysML v2 project provides an alternative implementation.

```bash
# Clone the Eclipse SysML v2 repository
git clone https://github.com/eclipse-syson/syson.git
cd syson

# Follow the build instructions in the repository
# (This implementation uses Eclipse Sirius and may have different setup requirements)
```

## Verifying the Installation

### Check API Health

```bash
# Test the API is running
curl http://localhost:9000/health

# Get API version
curl http://localhost:9000/api/v1/version

# List projects
curl http://localhost:9000/api/v1/projects
```

### Using sysml2pytest CLI

```bash
# Test connection with sysml2pytest
sysml2pytest extract \
  --api-url http://localhost:9000 \
  --project-id test-project \
  --output requirements.json
```

## Creating Sample Projects

### Using the Web Interface

1. Navigate to `http://localhost:9000` in your browser
2. Access the Swagger UI at `http://localhost:9000/swagger-ui.html`
3. Use the REST API to create projects and upload models

### Using cURL

```bash
# Create a new project
curl -X POST http://localhost:9000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ChristmasTreeProject",
    "description": "Example project for requirements"
  }'

# Upload a SysML V2 model file
curl -X POST http://localhost:9000/api/v1/projects/{project-id}/commits \
  -H "Content-Type: multipart/form-data" \
  -F "file=@christmas_tree_requirements.sysml"
```

### Sample SysML V2 Model

Create a file `sample_requirements.sysml`:

```sysml
package ChristmasTreeRequirements {

    requirement def TreeHeightRequirement {
        doc /* The Christmas tree shall be at least 150 cm and maximum 200 cm high. */

        attribute treeHeight : ScalarValues::Integer;

        require constraint {
            150 <= treeHeight and treeHeight <= 200
        }
    }

    requirement def OrnamentCountRequirement {
        doc /* The Christmas tree shall have between 20 and 100 ornaments. */

        attribute ornamentCount : ScalarValues::Integer;

        require constraint {
            ornamentCount >= 20 and ornamentCount <= 100
        }
    }
}
```

Upload this to your SysML V2 API server using the web interface or API calls.

## Configuration

### Database Options

The SysML V2 API can use different database backends:

**H2 (Default - In-Memory):**
```bash
java -jar sysml-v2-api-server.jar
# Data is not persisted between restarts
```

**PostgreSQL (Production):**
```bash
# Start PostgreSQL
docker run --name sysml-postgres \
  -e POSTGRES_PASSWORD=sysml \
  -e POSTGRES_DB=sysmldb \
  -p 5432:5432 \
  -d postgres:15

# Run API with PostgreSQL
java -jar sysml-v2-api-server.jar \
  --spring.datasource.url=jdbc:postgresql://localhost:5432/sysmldb \
  --spring.datasource.username=postgres \
  --spring.datasource.password=sysml
```

### Authentication

For production deployments, enable authentication:

```bash
java -jar sysml-v2-api-server.jar \
  --security.enabled=true \
  --security.oauth2.client.registration.keycloak.client-id=sysml-client \
  --security.oauth2.client.registration.keycloak.client-secret=secret
```

Then use API tokens:

```bash
# Extract with authentication
sysml2pytest extract \
  --api-url http://localhost:9000 \
  --api-token "your-token-here" \
  --project-id my-project \
  --output requirements.json
```

## Troubleshooting

### Port Already in Use

```bash
# Find process using port 9000
lsof -i :9000
# or
netstat -ano | grep 9000

# Kill the process or use different port
java -jar sysml-v2-api-server.jar --server.port=9001
```

### Java Version Issues

```bash
# Check Java version
java -version

# Ensure Java 17+
update-alternatives --config java  # Linux
```

### Connection Refused

```bash
# Check if server is running
curl http://localhost:9000/health

# Check firewall
sudo ufw status
sudo ufw allow 9000
```

### CORS Issues (Web Interface)

Add CORS configuration:

```bash
java -jar sysml-v2-api-server.jar \
  --cors.allowed-origins=http://localhost:3000
```

## Development Setup

For active development, use Docker Compose:

```yaml
# docker-compose.yml
version: '3.8'

services:
  sysml-api:
    image: sysml/sysml-v2-api-server:latest
    ports:
      - "9000:9000"
    environment:
      - SPRING_DATASOURCE_URL=jdbc:postgresql://postgres:5432/sysmldb
      - SPRING_DATASOURCE_USERNAME=postgres
      - SPRING_DATASOURCE_PASSWORD=sysml
    depends_on:
      - postgres
    volumes:
      - ./models:/models

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_PASSWORD=sysml
      - POSTGRES_DB=sysmldb
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

Run with:
```bash
docker-compose up -d
```

## Integration with sysml2pytest

### Complete Workflow Example

```bash
# 1. Start SysML V2 API
docker run -d -p 9000:9000 sysml/sysml-v2-api-server:latest

# 2. Wait for API to be ready
sleep 10

# 3. Create a project and upload model
# (Use web interface or API calls)

# 4. Extract requirements
sysml2pytest extract \
  --api-url http://localhost:9000 \
  --project-id christmas-tree-project \
  --output requirements.json

# 5. Generate tests
sysml2pytest generate \
  --input requirements.json \
  --output-dir tests/ \
  --system-module examples.system.christmas_tree

# 6. Run tests
pytest tests/ --requirement-trace=trace.json
```

## API Endpoints Reference

### Projects
- `GET /api/v1/projects` - List all projects
- `POST /api/v1/projects` - Create new project
- `GET /api/v1/projects/{id}` - Get project details
- `DELETE /api/v1/projects/{id}` - Delete project

### Commits
- `GET /api/v1/projects/{id}/commits` - List commits
- `POST /api/v1/projects/{id}/commits` - Create commit (upload model)
- `GET /api/v1/projects/{id}/commits/{commitId}` - Get commit details

### Elements
- `GET /api/v1/projects/{id}/commits/{commitId}/elements` - Get all elements
- `GET /api/v1/projects/{id}/commits/{commitId}/elements/{elementId}` - Get specific element
- `GET /api/v1/projects/{id}/commits/{commitId}/elements?type=RequirementDefinition` - Filter by type

### Query
- `POST /api/v1/projects/{id}/query` - Execute query to find elements

## Resources

- **Official SysML v2 Release**: https://github.com/Systems-Modeling/SysML-v2-Release
- **SysML v2 Specification**: https://www.omgsysml.org/
- **API Documentation**: http://localhost:9000/swagger-ui.html (when running)
- **Eclipse SysON**: https://github.com/eclipse-syson/syson
- **SysML v2 Pilot Implementation**: https://github.com/Systems-Modeling/SysML-v2-Pilot-Implementation

## Next Steps

1. **Start the API server** using one of the methods above
2. **Verify connectivity** with curl or the web interface
3. **Upload sample models** or use the examples in `sysml2pytest/examples/models/`
4. **Run sysml2pytest** to extract requirements and generate tests

For issues or questions, refer to the official SysML v2 community forums or GitHub issues.
