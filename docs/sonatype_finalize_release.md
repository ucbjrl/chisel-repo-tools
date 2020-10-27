# Finalize the Release on Sonatype

### Steps
- login to oss.sonatype.org
- select staging repositories
- select edu.berkeley.cs
- select individual staging repository items & verify content
- get sha of top level chisel-release commit
- git log -1
- For example:
- 2b1450bea5f6f87d99b1a07fe18f54190189c470- 
- select all staging repository items & click Close
- paste sha, version, and date into dialog box & click confirm
- Example
- 6b6f24376c3ac044c16bcc7e0b7e7b5ed282a5c0
- 3.4.0-RC1
- 20200816

- select individual staging repository item and monitor actions (requires clicking on Refresh)

- if errors
  - diagnose error
  - delete (control click) failing artifacts (on Sonatype)
  - fix errors
  - push fixed submodules
  - close fixed submodules (on Sonatype)
 
 - select all staging repository items & click Release

