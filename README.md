# wbd-assignment

## Exercise 1 - Python Web Server

For this exercise, I dug into the source code for the http module to look to see what methods I would have to define from the parent class for HTTP request handlers to supply a simple response.  The info log output when starting the server seemed like it was something that would easily be a logger method call to produce, but I had to write that out with some tricky f-strings.

Server responses match what is expected.

## Exercise 2 - Dockerfile

The Dockerfile needed for the image that can be used to run this server is very minimal as the Python module used is included in the package packages that come with the interpreter.  I chose the Python 3.12 lightweight image as a base since it's a trusted source, rather than using a user-made image.  For security best practices, I updated the image and cleaned out the nonsense then created a non-root user for the image to execute under to minimize privilege.  

The image was scanned with Hadolint which found no issues.  Not very surprising since there's isn't much going on in the Dockerfile.

## Exercise 3 - Helm chart

The Helm chart, too, is extremely minimal for the application.  There really isn't much to secure since there no dependencies or secrets or anything sensitive necessary to run this very lightweight app.  As a best practice, I signed the Helm package with a local GPG key.

## Exercise 4 - GitHub Workflows

For this exercise, I wasn't entirely what was expected for the build and deploy implementations, so I figured the "build" could be the construction of our image from the Dockerfile in exercise 2.  The deploy would just be the deployment of the web server using the image we built.  

## Exercise 5 - K8s RBAC

This exercise called for two cluster roles, one for a developer and one read-only.  Pretty straightforward, scoped the dev to a namespace and only granted access to deployments in there and the read-only role gets to see everything except secrets.

## Exercise 6 - AWS S3 Bucket Remediation IaC

This one was cool.  Using Terraform, I set up a little stack with an AWS Config rule in it that would remediate buckets found that are publicly accessible (really, this would be split into a "checker" and a "remediator" function, but combined the two just for the sake of clarity).  The Config rule uses a custom Lambda function to evaluate complaince (and remediate if necessary).  The rule was given an input parameter of what I'm considering to be the "public" tag to see if the bucket should be allowed to be publicly accessible.  The rule triggers on configuration changes, looks at the bucket's public access blocks and enables them if there are any not set.
