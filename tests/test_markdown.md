# Markdown Test File

This is a comprehensive test file for the HIAI markdown formatter.

## Headers

### H3 Header

#### H4 Header

##### H5 Header

## Text Formatting

**Bold text**
*Italic text*
***Bold and italic***
~~Strikethrough text~~
`Inline code`

## Links and Images

[Link to example](https://example.com)
![Alt text](image.jpg)

## Lists

### Unordered List
- Item 1
- Item 2
  - Nested item
  - Another nested item
- Item 3

### Ordered List
1. First item
2. Second item
   1. Nested item
   2. Another nested item
3. Third item

## Code Blocks

### Python
```python
def hello_world():
    """Print hello world"""
    print("Hello, World!")
    return True

class MyClass:
    def __init__(self):
        self.value = 42
    
    def method(self):
        # This is a comment
        return self.value * 2
```

### JavaScript
```javascript
const fetchData = async () => {
    try {
        const response = await fetch('/api/data');
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error:', error);
        throw error;
    }
};
```

### Bash
```bash
#!/bin/bash
# Deploy script
echo "Starting deployment..."

if [ -d "./dist" ]; then
    echo "Build directory found"
    cp -r ./dist/* /var/www/html/
else
    echo "Error: Build directory not found"
    exit 1
fi

echo "Deployment complete!"
```

### JSON
```json
{
    "name": "test-project",
    "version": "1.0.0",
    "dependencies": {
        "express": "^4.18.0",
        "lodash": "^4.17.21"
    },
    "scripts": {
        "start": "node index.js",
        "test": "jest"
    },
    "private": true
}
```

### YAML
```yaml
database:
  host: localhost
  port: 5432
  name: myapp
  credentials:
    username: admin
    password: secret
    
services:
  - web
  - api
  - worker
    
features:
  authentication: true
  caching: false
  logging: true
```

### Rust
```rust
fn main() {
    let mut count = 0;
    
    // Loop example
    for i in 0..10 {
        if i % 2 == 0 {
            println!("{} is even", i);
        } else {
            println!("{} is odd", i);
        }
        count += 1;
    }
    
    // Match example
    match count {
        0 => println!("Zero"),
        1 | 2 => println!("One or two"),
        _ => println!("Many"),
    }
}
```

### Go
```go
package main

import (
    "fmt"
    "net/http"
)

func helloHandler(w http.ResponseWriter, r *http.Request) {
    fmt.Fprintf(w, "Hello, %s!", r.URL.Path[1:])
}

func main() {
    http.HandleFunc("/", helloHandler)
    http.ListenAndServe(":8080", nil)
}
```

## Tables

| Name | Age | City |
|------|-----|------|
| John | 25 | New York |
| Jane | 30 | London |
| Bob | 35 | Paris |

## Blockquotes

> This is a blockquote
> 
> It can span multiple lines
> 
> > And can be nested

## Horizontal Rule

---

## Mixed Content

Here's a paragraph with **bold**, *italic*, and `code` elements.

- List item with **bold** and `code`
- Another item with [a link](https://example.com)

```python
# Code block after list
def test():
    pass
```

> Blockquote with `code` and **bold**

| Table | With | Various |
|-------|------|---------|
| **bold** | *italic* | `code` |