# ComfyUI Registry Standards

## Base Standards

Custom nodes in the ComfyUI registry must meet several foundational requirements:

### Community Value
Nodes should provide meaningful functionality to the community. Publishers should avoid excessive self-promotion, impersonation, or malicious behavior. Any self-promotional content belongs only in designated settings menu sections, while top and side menus should contain exclusively useful features.

### Node Compatibility
Custom nodes must not interfere with other nodes' installation, updates, or removal processes. When dependencies exist, developers should display clear warnings and provide example workflows demonstrating the required nodes.

### Legal Compliance
All submissions must comply with applicable laws and regulations.

### Quality Requirements
Nodes must be fully functional, well-documented, and actively maintained by their developers.

### Fork Guidelines
Forked nodes require clearly distinct names from originals and must offer significant functional or code differences.

## Security Standards

The registry enforces strict security policies requiring developers to rewrite non-compliant nodes:

### eval/exec Prohibition
"The use of `eval` and `exec` functions is prohibited in custom nodes due to security concerns." These enable arbitrary code execution, creating Remote Code Execution vulnerabilities exploitable for keylogging, ransomware, and other attacks.

### subprocess pip Installation Ban
Runtime package installation via subprocess is not allowed. ComfyUI Manager handles centralized dependency management, preventing supply chain attacks and eliminating multiple reload requirements.

### Code Obfuscation Prohibition
Obfuscated code cannot be reviewed and is presumed malicious, making it ineligible for publication.

Developers needing core functionality exposure should request features through the ComfyUI RFC repository.
