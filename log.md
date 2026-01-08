🚀 Initializing build environment
🌐 Setting up network
📦 Preparing dependencies
⚡ Inspecting MCP code
🔧 Preparing application build
📋 Setting up build checks
🎯 Initializing encrypted variables
✨ Optimizing bundle size
🔍 Inspecting manifest
🎉 Finalizing build setup
🚀 Build started for deployment: fastnotion-mcp
⚙️ Build configuration:
  • Repository: https://github.com/whjwjx/notionMCP
  • Entrypoint: notion_mcp.py
  • Python version: 3.12
  • Git SHA: e2b95271
  • Billing type: HOBBY
  • Environment variables: DATABASE_ID, NOTION_TOKEN
📦 Auto-detecting Python dependencies (will look for pyproject.toml, then requirements.txt)...
Authenticating with container registries...
Downloading your code...
Cloning into '.'...
From https://github.com/whjwjx/notionMCP
 * branch            e2b95271aee09e941c9c40ba830583c1ebce7fe9 -> FETCH_HEAD
HEAD is now at e2b9527 fix: 添加nest-asyncio解决异步环境运行冲突问题
Looking for Python dependencies...
Found requirements.txt for Python dependencies
DETECTED_REQUIREMENTS=requirements.txt
Build started on `date`
Preparing Python dependencies...
    cat > Dockerfile << 'EOF'
    FROM 342547628772.dkr.ecr.us-east-1.amazonaws.com/fastmcp-prd-base-images:mcp-base-python3.12
ARG HOME
ARG DATABASE_ID
ARG NOTION_TOKEN
ARG FASTMCP_CLOUD_URL
ARG FASTMCP_CLOUD_GIT_COMMIT_SHA
ARG FASTMCP_CLOUD_GIT_REPO
ARG DETECTED_REQUIREMENTS
# Copy application code
COPY . .
# Install FastMCP CLI for inspection
RUN uv pip install --system "fastmcp==2.12.3"
# Install dependencies from requirements file
RUN if [ -n "$DETECTED_REQUIREMENTS" ]; then \
        echo "Installing Python dependencies from $DETECTED_REQUIREMENTS..." && \
        if [ "$DETECTED_REQUIREMENTS" = "requirements.txt" ]; then \
            uv pip install --system -r "$DETECTED_REQUIREMENTS"; \
        elif [ "$DETECTED_REQUIREMENTS" = "pyproject.toml" ]; then \
            if grep -Eq '^\s*\[build-system\]' "pyproject.toml"; then \
                echo "Detected build-system; installing package from project root..." && \
                uv pip install --system .; \
            else \
                echo "No build-system; installing deps only from pyproject.toml..." && \
                uv pip install --system -r "pyproject.toml"; \
            fi; \
        else \
            echo "Unknown DETECTED_REQUIREMENTS value: $DETECTED_REQUIREMENTS"; \
        fi; \
    else \
        echo "No Python dependencies to install"; \
    fi
ENV HOME=$HOME
ENV DATABASE_ID=$DATABASE_ID
ENV NOTION_TOKEN=$NOTION_TOKEN
ENV FASTMCP_CLOUD_URL=$FASTMCP_CLOUD_URL
ENV FASTMCP_CLOUD_GIT_COMMIT_SHA=$FASTMCP_CLOUD_GIT_COMMIT_SHA
ENV FASTMCP_CLOUD_GIT_REPO=$FASTMCP_CLOUD_GIT_REPO
# Inspect MCP tools (continue build if this fails)
RUN fastmcp inspect -f fastmcp -o /tmp/server-info.json "/app/notion_mcp.py" || echo '{"error": "Failed to inspect MCP tools"}' > /tmp/server-info.json
# Lambda Web Adapter expects port 8080 by default
EXPOSE 8080
EOF
Creating Dockerfile...
Building your MCP server...
#0 building with "default" instance using docker driver
#1 [internal] load build definition from Dockerfile
#1 transferring dockerfile: 2.06kB done
#1 DONE 0.0s
#2 [auth] sharing credentials for 342547628772.dkr.ecr.us-east-1.amazonaws.com
#2 DONE 0.0s
#3 [internal] load metadata for 342547628772.dkr.ecr.us-east-1.amazonaws.com/fastmcp-prd-base-images:mcp-base-python3.12
#3 DONE 0.3s
#4 [internal] load .dockerignore
#4 transferring context: 2B done
#4 DONE 0.0s
#5 [internal] load build context
#5 transferring context: 200.84kB 0.0s done
#5 DONE 0.0s
#6 [1/5] FROM 342547628772.dkr.ecr.us-east-1.amazonaws.com/fastmcp-prd-base-images:mcp-base-python3.12@sha256:0f1c47d7bc4472be70c236a2ec54d192dcaf5cffb0e904a84feff2ca5c3e8ee3
#6 resolve 342547628772.dkr.ecr.us-east-1.amazonaws.com/fastmcp-prd-base-images:mcp-base-python3.12@sha256:0f1c47d7bc4472be70c236a2ec54d192dcaf5cffb0e904a84feff2ca5c3e8ee3 0.0s done
#6 sha256:47d2daa5f3238cad1d0d197d938b6cb597b5f923b201413ad2590f68f7f2836c 1.05MB / 30.78MB 0.2s
#6 sha256:fe2d526e7d41df5bda23740a00f6b254c44f67ce9bfc9507b36fb77c3b4c38e8 1.29MB / 1.29MB 0.2s done
#6 sha256:9d3a004b395bf1999d6d24b28ffa7dd319ab1f2acbad0d04d815d6c5ad4d3797 9.50kB / 9.50kB done
#6 sha256:0f1c47d7bc4472be70c236a2ec54d192dcaf5cffb0e904a84feff2ca5c3e8ee3 3.68kB / 3.68kB done
#6 sha256:61a9f733534e478a7570aaf3a154be5b9302dcf474e1fe0a827d4b146543b40e 0B / 12.11MB 0.1s
#6 sha256:d7c2baa095fbf75d83cd43b216be2d72bef124518338e23288648addadb8ee18 0B / 250B 0.2s
#6 sha256:47d2daa5f3238cad1d0d197d938b6cb597b5f923b201413ad2590f68f7f2836c 12.58MB / 30.78MB 0.3s
#6 sha256:61a9f733534e478a7570aaf3a154be5b9302dcf474e1fe0a827d4b146543b40e 6.29MB / 12.11MB 0.3s
#6 sha256:d7c2baa095fbf75d83cd43b216be2d72bef124518338e23288648addadb8ee18 250B / 250B 0.3s done
#6 sha256:14df781256a61534a5bb9cf46ed4a06652c502ff64f8a5b8c07b2e99a1f5cc06 0B / 1.70MB 0.3s
#6 sha256:47d2daa5f3238cad1d0d197d938b6cb597b5f923b201413ad2590f68f7f2836c 30.78MB / 30.78MB 0.4s
#6 sha256:61a9f733534e478a7570aaf3a154be5b9302dcf474e1fe0a827d4b146543b40e 12.11MB / 12.11MB 0.4s done
#6 sha256:14df781256a61534a5bb9cf46ed4a06652c502ff64f8a5b8c07b2e99a1f5cc06 1.70MB / 1.70MB 0.4s
#6 sha256:732ef97cdc451454bacb210aeeb1240b3176677a22f54bc1b91a8ca38149819a 0B / 34.77MB 0.4s
#6 extracting sha256:47d2daa5f3238cad1d0d197d938b6cb597b5f923b201413ad2590f68f7f2836c
#6 sha256:47d2daa5f3238cad1d0d197d938b6cb597b5f923b201413ad2590f68f7f2836c 30.78MB / 30.78MB 0.4s done
#6 sha256:14df781256a61534a5bb9cf46ed4a06652c502ff64f8a5b8c07b2e99a1f5cc06 1.70MB / 1.70MB 0.4s done
#6 sha256:076c77164319d2881c7bfd71d84caee401a7caaa1185fcc2eab24d2a5f2effbc 0B / 19.37MB 0.5s
#6 sha256:7f9db5bbba9612fd8f4a988f95bd0cd06378335232380f372f7774a0f93b9f1d 0B / 19.87MB 0.5s
#6 sha256:732ef97cdc451454bacb210aeeb1240b3176677a22f54bc1b91a8ca38149819a 12.58MB / 34.77MB 0.7s
#6 sha256:076c77164319d2881c7bfd71d84caee401a7caaa1185fcc2eab24d2a5f2effbc 11.53MB / 19.37MB 0.7s
#6 sha256:7f9db5bbba9612fd8f4a988f95bd0cd06378335232380f372f7774a0f93b9f1d 14.68MB / 19.87MB 0.7s
#6 sha256:732ef97cdc451454bacb210aeeb1240b3176677a22f54bc1b91a8ca38149819a 20.97MB / 34.77MB 0.8s
#6 sha256:076c77164319d2881c7bfd71d84caee401a7caaa1185fcc2eab24d2a5f2effbc 18.87MB / 19.37MB 0.8s
#6 sha256:7f9db5bbba9612fd8f4a988f95bd0cd06378335232380f372f7774a0f93b9f1d 19.87MB / 19.87MB 0.8s
#6 sha256:732ef97cdc451454bacb210aeeb1240b3176677a22f54bc1b91a8ca38149819a 34.77MB / 34.77MB 0.9s done
#6 sha256:076c77164319d2881c7bfd71d84caee401a7caaa1185fcc2eab24d2a5f2effbc 19.37MB / 19.37MB 0.9s done
#6 sha256:7f9db5bbba9612fd8f4a988f95bd0cd06378335232380f372f7774a0f93b9f1d 19.87MB / 19.87MB 0.8s done
#6 sha256:24a969d77be0fc77d0f41270e4683d95a934abf872d257dac580b48948867cdb 93B / 93B 1.0s done
#6 sha256:2f2244bb02d09fcb8c6445e7d36effbde3dc6e01f5518b0d49d768081103c228 0B / 17.90MB 1.0s
#6 sha256:ba1a050f9d6b356dd21a23020bb00ce1312b8c878a2b0e37ef1e243e468cd640 126.36kB / 126.36kB 1.0s done
#6 sha256:577967057cde4177f5d7b031da9f0f7014c999272ef8229db2bb312e379e3670 0B / 29.23kB 1.0s
#6 sha256:006edb831cba29223a193a0f479f304e07683f4076f1b1de0add12cd6f0899ac 0B / 822.44kB 1.0s
#6 sha256:2f2244bb02d09fcb8c6445e7d36effbde3dc6e01f5518b0d49d768081103c228 4.19MB / 17.90MB 1.1s
#6 sha256:577967057cde4177f5d7b031da9f0f7014c999272ef8229db2bb312e379e3670 29.23kB / 29.23kB 1.0s done
#6 sha256:006edb831cba29223a193a0f479f304e07683f4076f1b1de0add12cd6f0899ac 822.44kB / 822.44kB 1.1s done
#6 sha256:da1a2373221d7183d24e676a226aa9858b0b28489c084ec93cffcdd8743a130a 0B / 1.15kB 1.1s
#6 sha256:9caacfc0a660265e982a9db6a6b7837eaceb348a597b2b7ef40a3c46b5d1ea03 0B / 174B 1.1s
#6 sha256:2f2244bb02d09fcb8c6445e7d36effbde3dc6e01f5518b0d49d768081103c228 17.90MB / 17.90MB 1.2s
#6 sha256:da1a2373221d7183d24e676a226aa9858b0b28489c084ec93cffcdd8743a130a 1.15kB / 1.15kB 1.1s done
#6 sha256:9caacfc0a660265e982a9db6a6b7837eaceb348a597b2b7ef40a3c46b5d1ea03 174B / 174B 1.1s done
#6 sha256:065fb440b3398a7e33c3c80b51174578f6c29db1bead47fd4d10861563cf771d 1.15kB / 1.15kB 1.2s
#6 sha256:2f2244bb02d09fcb8c6445e7d36effbde3dc6e01f5518b0d49d768081103c228 17.90MB / 17.90MB 1.2s done
#6 sha256:065fb440b3398a7e33c3c80b51174578f6c29db1bead47fd4d10861563cf771d 1.15kB / 1.15kB 1.2s done
#6 extracting sha256:47d2daa5f3238cad1d0d197d938b6cb597b5f923b201413ad2590f68f7f2836c 1.5s done
#6 extracting sha256:fe2d526e7d41df5bda23740a00f6b254c44f67ce9bfc9507b36fb77c3b4c38e8
#6 extracting sha256:fe2d526e7d41df5bda23740a00f6b254c44f67ce9bfc9507b36fb77c3b4c38e8 0.1s done
#6 extracting sha256:61a9f733534e478a7570aaf3a154be5b9302dcf474e1fe0a827d4b146543b40e
#6 extracting sha256:61a9f733534e478a7570aaf3a154be5b9302dcf474e1fe0a827d4b146543b40e 0.6s done
#6 extracting sha256:d7c2baa095fbf75d83cd43b216be2d72bef124518338e23288648addadb8ee18
#6 extracting sha256:d7c2baa095fbf75d83cd43b216be2d72bef124518338e23288648addadb8ee18 done
#6 extracting sha256:14df781256a61534a5bb9cf46ed4a06652c502ff64f8a5b8c07b2e99a1f5cc06 0.1s done
#6 extracting sha256:732ef97cdc451454bacb210aeeb1240b3176677a22f54bc1b91a8ca38149819a
#6 extracting sha256:732ef97cdc451454bacb210aeeb1240b3176677a22f54bc1b91a8ca38149819a 1.2s done
#6 extracting sha256:076c77164319d2881c7bfd71d84caee401a7caaa1185fcc2eab24d2a5f2effbc
#6 extracting sha256:076c77164319d2881c7bfd71d84caee401a7caaa1185fcc2eab24d2a5f2effbc 0.8s done
#6 extracting sha256:7f9db5bbba9612fd8f4a988f95bd0cd06378335232380f372f7774a0f93b9f1d
#6 extracting sha256:7f9db5bbba9612fd8f4a988f95bd0cd06378335232380f372f7774a0f93b9f1d 0.4s done
#6 extracting sha256:24a969d77be0fc77d0f41270e4683d95a934abf872d257dac580b48948867cdb done
#6 extracting sha256:ba1a050f9d6b356dd21a23020bb00ce1312b8c878a2b0e37ef1e243e468cd640 0.0s done
#6 extracting sha256:2f2244bb02d09fcb8c6445e7d36effbde3dc6e01f5518b0d49d768081103c228 0.1s
#6 extracting sha256:2f2244bb02d09fcb8c6445e7d36effbde3dc6e01f5518b0d49d768081103c228 1.2s done
#6 extracting sha256:577967057cde4177f5d7b031da9f0f7014c999272ef8229db2bb312e379e3670
#6 extracting sha256:577967057cde4177f5d7b031da9f0f7014c999272ef8229db2bb312e379e3670 done
#6 extracting sha256:006edb831cba29223a193a0f479f304e07683f4076f1b1de0add12cd6f0899ac 0.0s done
#6 extracting sha256:9caacfc0a660265e982a9db6a6b7837eaceb348a597b2b7ef40a3c46b5d1ea03
#6 extracting sha256:9caacfc0a660265e982a9db6a6b7837eaceb348a597b2b7ef40a3c46b5d1ea03 done
#6 extracting sha256:da1a2373221d7183d24e676a226aa9858b0b28489c084ec93cffcdd8743a130a done
#6 extracting sha256:065fb440b3398a7e33c3c80b51174578f6c29db1bead47fd4d10861563cf771d done
#6 DONE 7.4s
#7 [2/5] COPY . .
#7 DONE 0.7s
#8 [3/5] RUN uv pip install --system "fastmcp==2.12.3"
#8 0.501 Using Python 3.12.12 environment at: /usr/local
#8 0.760 Resolved 60 packages in 256ms
#8 0.796 Prepared 9 packages in 34ms
#8 0.803 Uninstalled 1 package in 7ms
#8 0.816 Installed 9 packages in 12ms
#8 0.816  - fastmcp==2.14.2
#8 0.817  + fastmcp==2.12.3
#8 0.817  + isodate==0.7.2
#8 0.817  + lazy-object-proxy==1.12.0
#8 0.818  + markupsafe==3.0.3
#8 0.818  + openapi-core==0.22.0
#8 0.818  + openapi-schema-validator==0.6.3
#8 0.818  + openapi-spec-validator==0.7.2
#8 0.818  + rfc3339-validator==0.1.4
#8 0.818  + werkzeug==3.1.4
#8 DONE 1.0s
#9 [4/5] RUN if [ -n "requirements.txt" ]; then         echo "Installing Python dependencies from requirements.txt..." &&         if [ "requirements.txt" = "requirements.txt" ]; then             uv pip install --system -r "requirements.txt";         elif [ "requirements.txt" = "pyproject.toml" ]; then             if grep -Eq '^\s*\[build-system\]' "pyproject.toml"; then                 echo "Detected build-system; installing package from project root..." &&                 uv pip install --system .;             else                 echo "No build-system; installing deps only from pyproject.toml..." &&                 uv pip install --system -r "pyproject.toml";             fi;         else             echo "Unknown DETECTED_REQUIREMENTS value: requirements.txt";         fi;     else         echo "No Python dependencies to install";     fi
#9 0.261 Installing Python dependencies from requirements.txt...
#9 0.269 Using Python 3.12.12 environment at: /usr/local
#9 0.329 Resolved 62 packages in 57ms
#9 0.354 Prepared 2 packages in 24ms
#9 0.361 Installed 2 packages in 5ms
#9 0.361  + nest-asyncio==1.6.0
#9 0.361  + pypinyin==0.55.0
#9 DONE 0.5s
#10 [5/5] RUN fastmcp inspect -f fastmcp -o /tmp/server-info.json "/app/notion_mcp.py" || echo '{"error": "Failed to inspect MCP tools"}' > /tmp/server-info.json
#10 2.664 [01/08/26 12:44:36] INFO     Processing request of type            server.py:713
#10 2.664                              ListToolsRequest                                   
#10 2.666                     INFO     Processing request of type            server.py:713
#10 2.666                              ListPromptsRequest                                 
#10 2.668                     INFO     Processing request of type            server.py:713
#10 2.668                              ListResourcesRequest                               
#10 2.670                     INFO     Processing request of type            server.py:713
#10 2.670                              ListResourceTemplatesRequest                       
#10 2.675 [01/08/26 12:44:36] INFO     Server inspection complete. Report saved cli.py:756
#10 2.675                              to /tmp/server-info.json                           
#10 2.675 ✓ Server inspection saved to: /tmp/server-info.json
#10 2.676   Server: Notion MCP Server
#10 2.676   Format: fastmcp
#10 DONE 3.1s
#11 exporting to image
#11 exporting layers
#11 exporting layers 0.3s done
#11 writing image sha256:85e0fa98f1f1f2c6fc8f216e2068ef16716e5c1ec851999e1f49111767c5e626 done
#11 naming to 342547628772.dkr.ecr.us-east-1.amazonaws.com/fastmcp-prd-images:fastnotion-mcp-e2b95271 done
#11 DONE 0.3s
 [33m2 warnings found (use docker --debug to expand):
[0m - SecretsUsedInArgOrEnv: Do not use ARG or ENV instructions for sensitive data (ARG "NOTION_TOKEN") (line 5)
 - SecretsUsedInArgOrEnv: Do not use ARG or ENV instructions for sensitive data (ENV "NOTION_TOKEN") (line 41)
Build completed on `date`
Analyzing your MCP tools...
a1d69b6dbc25b7a1449ff9c3d7f88dd736b7ad7a3efbbbf36eabe645e03ba106
mcp-inspect-fastnotion-mcp-e2b95271
Publishing your MCP server...
The push refers to repository [342547628772.dkr.ecr.us-east-1.amazonaws.com/fastmcp-prd-images]
2b281c398352: Preparing
102855ee1193: Preparing
5032e12eb7a1: Preparing
0801921a8af1: Preparing
b853345817a0: Preparing
7ae6af6714a9: Preparing
9f1a66994505: Preparing
c64a640ec217: Preparing
2e66dc298b64: Preparing
349b010c6bf0: Preparing
c89fb50db8f8: Preparing
2c82198a9b91: Preparing
d40ba8acf843: Preparing
e00cb120f83c: Preparing
3ba52b69cfaa: Preparing
8cc89f5d2261: Preparing
04b3d4cdb969: Preparing
70ea44b91986: Preparing
25825f276be6: Preparing
6a7f953ae30c: Preparing
7ae6af6714a9: Waiting
9f1a66994505: Waiting
c64a640ec217: Waiting
2e66dc298b64: Waiting
349b010c6bf0: Waiting
c89fb50db8f8: Waiting
2c82198a9b91: Waiting
d40ba8acf843: Waiting
e00cb120f83c: Waiting
3ba52b69cfaa: Waiting
8cc89f5d2261: Waiting
04b3d4cdb969: Waiting
70ea44b91986: Waiting
25825f276be6: Waiting
6a7f953ae30c: Waiting
b853345817a0: Layer already exists
7ae6af6714a9: Layer already exists
9f1a66994505: Layer already exists
c64a640ec217: Layer already exists
2e66dc298b64: Layer already exists
349b010c6bf0: Layer already exists
0801921a8af1: Pushed
c89fb50db8f8: Layer already exists
2c82198a9b91: Layer already exists
d40ba8acf843: Layer already exists
e00cb120f83c: Layer already exists
3ba52b69cfaa: Layer already exists
04b3d4cdb969: Layer already exists
8cc89f5d2261: Layer already exists
102855ee1193: Pushed
70ea44b91986: Layer already exists
25825f276be6: Layer already exists
6a7f953ae30c: Layer already exists
2b281c398352: Pushed
5032e12eb7a1: Pushed
fastnotion-mcp-e2b95271: digest: sha256:9970541bc297227f2acfb9177edbf4d3b071b29e5a1f15748fd11509490b721b size: 4519
📦 Build artifacts uploaded successfully
🚀 Server build complete! Deploying server now...
✅ Server deployed successfully, starting pre-flight validation...
✈️ Starting pre-flight check to verify server startup...
Server failed to start properly - check the server logs for startup errors
❌ Pre-flight check failed - your MCP server may have startup issues. Check the server logs for detailed error information.