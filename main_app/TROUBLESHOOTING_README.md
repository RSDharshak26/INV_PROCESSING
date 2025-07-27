# 🐛 Troubleshooting Guide & Learning Points

This guide documents **all the errors we encountered** during the development of this invoice processing application, along with **solutions and key learning points** for new developers.

## 📚 Table of Contents
1. [Authentication & Credentials Errors](#authentication--credentials-errors)
2. [Docker & Container Issues](#docker--container-issues)
3. [Lambda & AWS Issues](#lambda--aws-issues)
4. [CORS & API Issues](#cors--api-issues)
5. [Image Processing Errors](#image-processing-errors)
6. [File System & Path Issues](#file-system--path-issues)
7. [Infrastructure & Deployment Issues](#infrastructure--deployment-issues)
8. [WebSocket Issues](#websocket-issues)
9. [Frontend Display Issues](#frontend-display-issues)
10. [Key Learning Points](#key-learning-points)

---

## 🔐 Authentication & Credentials Errors

### ❌ Error 1: Google Cloud Credentials Not Found
```
inv-processing-authentication-f9e50adadbc5.json was not found
```

**What Happened:** Docker couldn't find the Google Cloud service account key file.

**Root Cause:** File path in `docker-compose.yml` was incorrect or pointing to wrong filename.

**Solution:**
Google Cloud credentials are now retrieved from AWS Secrets Manager. Ensure that:
1. AWS credentials are properly configured in your environment
2. The secret "google_ocr" exists in AWS Secrets Manager (us-east-1 region)
3. Your AWS role/user has permissions to read from Secrets Manager

```yaml
# In docker-compose.yml - No Google credentials needed anymore
environment:
  - FLASK_APP=app.py
  - FLASK_ENV=production
```

**Learning Points:**
- AWS Secrets Manager provides better security than mounting credential files
- Ensure proper IAM permissions for Secrets Manager access
- Use absolute paths when possible
- Verify files exist before referencing them in configs

### ❌ Error 2: Invalid Grant - Expired Credentials
```
503 Getting metadata from plugin failed with error: ('invalid_grant: Bad Request', {'error': 'invalid_grant', 'error_description': 'Bad Request'})
```

**What Happened:** Google Cloud credentials were expired or invalid.

**Root Cause:** Service account key was old or corrupted.

**Solutions:**
1. **For Docker:** Restart containers to pick up new credentials
   ```powershell
   docker-compose down
   docker-compose up --build
   ```

2. **For Lambda:** Ensure proper IAM policies in SAM template
   ```yaml
   Policies:
     - SecretsManagerReadWrite  # For accessing Google OCR credentials
   ```

3. **For Local Development:** Configure AWS credentials
   ```powershell
   # Ensure AWS credentials are configured
   aws configure
   # Or set environment variables
   $env:AWS_ACCESS_KEY_ID="your_access_key"
   $env:AWS_SECRET_ACCESS_KEY="your_secret_key"
   $env:AWS_DEFAULT_REGION="us-east-1"
   ```

**Learning Points:**
- Credentials have expiration dates
- Different environments need different credential setups
- Always test credentials in each environment

---

## 🐳 Docker & Container Issues

### ❌ Error 3: Module Not Found in Container
```
ModuleNotFoundError: No module named 'serverless_wsgi'
```

**What Happened:** Python dependencies weren't installed in Docker container.

**Root Cause:** SAM wasn't building with the container or `requirements.txt` wasn't being used.

**Solutions:**
1. **Force container rebuild:**
   ```powershell
   sam build --use-container
   docker-compose up --build
   ```

2. **Verify requirements.txt exists and contains:**
   ```
   flask
   flask-cors
   google-cloud-vision==3.4.4
   serverless_wsgi
   boto3
   Pillow
   ```

**Learning Points:**
- Always use `--use-container` for SAM builds
- Force rebuilds when dependencies change
- Container environments are isolated from local environments

### ❌ Error 4: Version Mismatch Issues
```
Python version mismatch between local (3.12) and Lambda (3.9)
```

**What Happened:** Different Python versions between development and deployment.

**Solution:** Update SAM template runtime
```yaml
Runtime: python3.12  # Match your local version
```

**Learning Points:**
- Keep development and production environments in sync
- Document required versions in README
- Use version managers like pyenv for consistency

---

## ⚡ Lambda & AWS Issues

### ❌ Error 5: Wrong AWS Account Deployment
```
"YOU idiot. it was the wrong account. WHY THE FUCK IS IT GOING IN ANOTHER ACCOUNT"
```

**What Happened:** AWS CLI was configured with wrong account credentials.

**Root Cause:** Multiple AWS profiles or cached credentials pointing to different account.

**Solutions:**
1. **Check current account:**
   ```powershell
   aws sts get-caller-identity
   ```

2. **Reconfigure AWS CLI:**
   ```powershell
   aws configure
   # Enter correct Access Key ID and Secret
   ```

3. **Set default profile:**
   ```powershell
   aws configure set default.region us-east-1
   ```

4. **Delete resources from wrong account:**
   ```powershell
   aws cloudformation delete-stack --stack-name wrong-stack-name
   ```

**Learning Points:**
- Always verify AWS account before deployment
- AWS credentials can be cached and cause confusion
- Use `aws sts get-caller-identity` to confirm identity
- Multiple AWS accounts require careful profile management

### ❌ Error 6: Read-Only File System in Lambda
```
Read-only file system: 'temp_upload_1753333941.jpg'
```

**What Happened:** Tried to save files outside `/tmp/` directory in Lambda.

**Root Cause:** Lambda filesystem is read-only except for `/tmp/` directory.

**Solution:** Always use `/tmp/` for temporary files
```python
temp_path = f"/tmp/temp_upload_{int(time.time())}.jpg"
output_path = f"/tmp/output_{int(time.time())}.jpg"
```

**Learning Points:**
- Lambda has a read-only filesystem except `/tmp/`
- `/tmp/` has 512MB limit and gets cleaned up
- Plan file storage strategy for serverless functions

### ❌ Error 7: Security Constraints in API Gateway
```
Error: Security Constraints Not Satisfied!
```

**What Happened:** API Gateway required authentication but none was configured.

**Root Cause:** Missing authentication configuration in SAM template.

**Solution:** Add auth configuration or disable it
```yaml
Events:
  ReceiveApi:
    Type: Api
    Properties:
      Path: /receive
      Method: post
      # Either add auth or explicitly disable it
      Auth:
        ApiKeyRequired: false
```

**Learning Points:**
- API Gateway has security by default
- Explicitly configure authentication requirements
- Test API accessibility after deployment

---

## 🌐 CORS & API Issues

### ❌ Error 8: CORS Errors in Browser
```
Access to fetch at 'https://api.example.com' from origin 'https://frontend.com' has been blocked by CORS policy
```

**What Happened:** Browser blocked cross-origin requests.

**Root Cause:** Missing CORS headers in API responses.

**Solutions:**
1. **Add CORS headers to all responses:**
   ```python
   resp.headers['Access-Control-Allow-Origin'] = '*'
   resp.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
   resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
   ```

2. **Add OPTIONS preflight handler:**
   ```python
   @upload_bp.route('/receive', methods=['OPTIONS'])
   def handle_preflight():
       response = make_response()
       response.headers['Access-Control-Allow-Origin'] = '*'
       response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
       response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
       return response
   ```

3. **Configure Flask-CORS:**
   ```python
   from flask_cors import CORS
   CORS(app, origins=["*"])  # Allow all origins
   ```

**Learning Points:**
- CORS is a browser security feature
- Required for frontend-backend communication across domains
- Must handle both actual requests and OPTIONS preflight requests
- Different environments may need different CORS configurations

### ❌ Error 9: Binary Media Type Issues
```
PIL.UnidentifiedImageError: cannot identify image file
```

**What Happened:** API Gateway corrupted binary image data.

**Root Cause:** API Gateway wasn't configured to handle binary media types.

**Solution:** Add binary media types to API Gateway
```yaml
Globals:
  Api:
    BinaryMediaTypes:
      - image/*
      - application/octet-stream
      - multipart/form-data
```

**Learning Points:**
- API Gateway needs explicit binary media type configuration
- Images and files require special handling in serverless APIs
- Test file uploads thoroughly in different environments

---

## 🖼️ Image Processing Errors

### ❌ Error 10: PIL Cannot Open Image
```
PIL.UnidentifiedImageError: cannot identify image file
```

**What Happened:** PIL couldn't read the uploaded image file.

**Root Cause:** Multiple possible causes - corrupted data, wrong format, or file access issues.

**Solution:** Implement robust image opening with fallbacks
```python
def open_image_robust(image_path):
    try:
        # Method 1: Standard PIL open
        image = Image.open(image_path)
        return image.convert('RGB')
    except Exception:
        try:
            # Method 2: BytesIO approach
            with open(image_path, 'rb') as f:
                img_bytes = f.read()
            image = Image.open(io.BytesIO(img_bytes))
            return image.convert('RGB')
        except Exception:
            # Method 3: Force RGB conversion
            with Image.open(image_path) as img:
                return img.convert('RGB')
```

**Learning Points:**
- Image processing can fail in many ways
- Always implement fallback methods
- Convert images to RGB for consistency
- Test with various image formats (JPEG, PNG, WEBP, etc.)

### ❌ Error 11: Image Display Issues in Browser
```
Image shows as broken/not loading in frontend
```

**What Happened:** Frontend couldn't access image file saved in Lambda's `/tmp/` directory.

**Root Cause:** `/tmp/` files in Lambda are not accessible from web browsers.

**Solution:** Return image as base64 data
```python
# Backend: Convert to base64
import base64
buffered = io.BytesIO()
image.save(buffered, format="JPEG")
img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
return f"data:image/jpeg;base64,{img_base64}"

# Frontend: Display directly
<img src={base64ImageData} alt="Processed image" />
```

**Learning Points:**
- Lambda `/tmp/` files are not web-accessible
- Base64 encoding allows embedding images in responses
- Consider file size limits with base64 (increases size by ~33%)
- For large images, use S3 or other storage services

---

## 📁 File System & Path Issues

### ❌ Error 12: File Extension Mismatch
```
UnicodeDecodeError while processing HTTP request
```

**What Happened:** Saved file with wrong extension (e.g., saving JPG as .pdf).

**Root Cause:** Hard-coded file extension instead of detecting from uploaded file.

**Solution:** Extract extension dynamically
```python
import os
file_extension = os.path.splitext(file.filename)[1] or '.jpg'
temp_path = f"/tmp/temp_upload_{int(time.time())}{file_extension}"
```

**Learning Points:**
- Always preserve original file extensions
- Validate file types before processing
- Handle cases where extensions might be missing

### ❌ Error 13: File Saving Verification Issues
```
File was not saved to disk / Saved file is empty
```

**What Happened:** File save operation failed silently.

**Root Cause:** Disk space, permissions, or I/O errors.

**Solution:** Verify file after saving
```python
try:
    file.save(temp_path)
    
    # Verify file was saved
    if not os.path.exists(temp_path):
        raise Exception("File was not saved to disk")
    
    file_size = os.path.getsize(temp_path)
    if file_size == 0:
        raise Exception("Saved file is empty")
        
except Exception as save_error:
    # Alternative saving method
    with open(temp_path, 'wb') as f:
        file.seek(0)
        f.write(file.read())
        f.flush()
        os.fsync(f.fileno())  # Force write to disk
```

**Learning Points:**
- File operations can fail silently
- Always verify files after saving
- Implement alternative saving methods
- Check file sizes and existence

---

## 🏗️ Infrastructure & Deployment Issues

### ❌ Error 14: CloudFormation Template Errors
```
Transform AWS::Serverless-2016-10-31 failed with: Invalid Serverless Application Specification
```

**What Happened:** SAM template had configuration conflicts.

**Root Cause:** Conflicting authentication settings between global and method-level configurations.

**Solution:** Remove conflicting configurations
```yaml
# Remove method-level auth when global auth is not defined
Events:
  ReceiveApi:
    Type: Api
    Properties:
      Path: /receive
      Method: post
      # Remove: Auth: ApiKeyRequired: false
```

**Learning Points:**
- SAM templates have hierarchical configuration rules
- Global settings override method-level settings
- Validate templates before deployment
- Use SAM CLI to validate syntax: `sam validate`

### ❌ Error 15: Stack Deployment to Wrong Region/Account
```
Stack deployed to wrong AWS account
```

**What Happened:** AWS CLI configured with wrong credentials or region.

**Prevention Strategies:**
1. **Always verify before deployment:**
   ```powershell
   aws sts get-caller-identity
   aws configure list
   ```

2. **Use explicit parameters:**
   ```powershell
   aws cloudformation deploy --region us-east-1 --profile production
   ```

3. **Create deployment scripts with validations:**
   ```powershell
   # Check current account
   $account = aws sts get-caller-identity --query Account --output text
   if ($account -ne "your-expected-account-id") {
       Write-Error "Wrong AWS account!"
       exit 1
   }
   ```

**Learning Points:**
- Always double-check AWS configuration before deployment
- Use named profiles for different environments
- Implement safety checks in deployment scripts

---

## 🔌 WebSocket Issues

### ❌ Error 16: WebSocket Connection Failed
```
Failed to connect to WebSocket
```

**Common Causes & Solutions:**

1. **Wrong WebSocket URL format:**
   ```javascript
   // Wrong: https://...
   // Correct: wss://api-id.execute-api.region.amazonaws.com/stage
   const ws = new WebSocket('wss://abc123.execute-api.us-east-1.amazonaws.com/dev')
   ```

2. **Missing route configurations:**
   ```yaml
   # Ensure all routes are properly configured
   ConnectRoute:
     Type: AWS::ApiGatewayV2::Route
     Properties:
       RouteKey: $connect
   ```

3. **IAM permission issues:**
   ```yaml
   # Lambda needs execute-api permissions
   - Effect: Allow
     Action: execute-api:ManageConnections
     Resource: !Sub "arn:aws:execute-api:${AWS::Region}:${AWS::AccountId}:${WebSocketApi}/*"
   ```

**Learning Points:**
- WebSocket URLs use `wss://` protocol, not `https://`
- WebSocket APIs require different configuration than REST APIs
- Test connections with online WebSocket testing tools
- Check CloudWatch logs for connection errors

---

## 🖥️ Frontend Display Issues

### ❌ Error 17: Image Not Displaying in Results
```
Processed image shows as broken in browser
```

**What Happened:** Frontend trying to load image from inaccessible Lambda `/tmp/` path.

**Root Cause:** Lambda temporary files are not web-accessible.

**Evolution of Solutions:**

1. **Initial (Wrong) Approach:**
   ```javascript
   // Trying to load from Lambda /tmp/ - doesn't work!
   <img src={`http://localhost:5000/tmp/output.jpg`} />
   ```

2. **Corrected Approach:**
   ```javascript
   // Display base64 image data directly
   <img src={base64ImageData} alt="Processed image" />
   ```

**Backend Changes:**
```python
# Old: Return file path
return {"image_url": "/tmp/output.jpg"}

# New: Return base64 data
return {"processed_image": "data:image/jpeg;base64,iVBORw0KGgoA..."}
```

**Learning Points:**
- Serverless functions don't serve static files
- Base64 encoding allows embedding binary data in JSON responses
- Consider response size limits with base64 encoding
- For production, use CDN/S3 for large images

---

## 🎯 Key Learning Points

### 🏗️ **Architecture Patterns**

1. **Serverless Constraints:**
   - Read-only filesystem except `/tmp/`
   - Limited execution time
   - No persistent storage
   - Stateless design required

2. **Cross-Origin Resource Sharing (CORS):**
   - Required for frontend-backend communication
   - Must handle both requests and preflight OPTIONS
   - Different environments need different configurations

3. **File Handling in Cloud:**
   - Temporary files disappear after function execution
   - Use S3 for persistent storage
   - Base64 for small images, signed URLs for large ones

### 🔧 **Development Best Practices**

1. **Error Handling:**
   ```python
   try:
       # Primary method
       result = risky_operation()
   except SpecificError as e:
       # Fallback method
       result = safe_fallback()
   except Exception as e:
       # Log and re-raise
       print(f"Unexpected error: {e}")
       raise
   ```

2. **Environment Configuration:**
   - Use environment variables for configuration
   - Different settings for dev/staging/production
   - Never hard-code sensitive values

3. **Testing Strategy:**
   - Test in each environment (local, Lambda, production)
   - Use different file types and sizes
   - Test edge cases (empty files, large files, wrong formats)

### 🚀 **Deployment Strategies**

1. **Infrastructure as Code:**
   - Use SAM/CloudFormation for reproducible deployments
   - Version control all infrastructure code
   - Validate templates before deployment

2. **CI/CD Pipeline:**
   - Automate testing and deployment
   - Include environment checks
   - Rollback strategies for failed deployments

3. **Monitoring & Debugging:**
   - Use CloudWatch logs extensively
   - Add meaningful log messages
   - Monitor performance metrics

### 🔐 **Security Considerations**

1. **Credentials Management:**
   - Use IAM roles instead of hardcoded keys
   - Rotate credentials regularly
   - Different credentials for different environments

2. **API Security:**
   - Implement proper authentication
   - Validate all inputs
   - Use HTTPS everywhere

3. **Data Handling:**
   - Don't log sensitive data
   - Encrypt data in transit and at rest
   - Clean up temporary files

### 📊 **Performance Optimization**

1. **Lambda Optimization:**
   - Minimize cold starts
   - Optimize memory allocation
   - Use connection pooling

2. **Image Processing:**
   - Compress images appropriately
   - Use appropriate formats (JPEG vs PNG)
   - Consider image size limits

3. **API Design:**
   - Implement proper caching
   - Use pagination for large datasets
   - Optimize response sizes

---

## 🎉 **Success Metrics**

After resolving all these issues, we successfully built:

✅ **A production-ready invoice processing system**  
✅ **Real-time WebSocket dashboard**  
✅ **Robust error handling and fallbacks**  
✅ **Automated CI/CD pipeline**  
✅ **Scalable serverless architecture**  
✅ **Cross-platform compatibility**  

### 🚀 **Key Takeaways for New Developers**

1. **Expect and Plan for Errors** - They're part of the learning process
2. **Test Everything in Multiple Environments** - Local ≠ Production
3. **Read Error Messages Carefully** - They usually tell you what's wrong
4. **Use Version Control** - So you can revert when things break
5. **Document Everything** - Your future self will thank you
6. **Start Simple, Add Complexity Gradually** - Get basics working first
7. **Learn Cloud Platform Constraints** - Each service has limitations
8. **Security First** - Don't leave it for later
9. **Monitor and Log** - You can't fix what you can't see
10. **Ask for Help** - The community is usually very helpful!

**Remember: Every error is a learning opportunity! 🌟**

---

*This guide represents real-world development challenges and solutions. Keep it handy for future reference and contribute to it as you encounter new issues!* 