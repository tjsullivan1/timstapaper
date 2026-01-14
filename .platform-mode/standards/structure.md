# Structure

Environment & Naming:
- What environment is this for (dev, staging, prod)?
- What naming convention would you prefer for resources?
- What Azure region should this be deployed in?

Network Configuration:
- Do you have an existing VNet you want to use, or should the module create a new one?
- What CIDR ranges would you prefer for the VNet and AKS subnet?
- Do you need additional subnets (e.g., for Application Gateway, Azure Firewall)?

AKS Configuration:
- What node pool configuration do you need (VM size, node count, scaling limits)?
- Do you need system and user node pools separated?
- What Kubernetes version should be used?

Security & Access:
- What level of network policies do you need (Azure CNI, Calico)?
- Do you need Azure AD integration for RBAC?
- Should the module create a new service principal or use an existing one?

DNS & Connectivity:
- Do you have an existing private DNS zone for AKS, or should the module create one?
- Do you need a jumpbox or bastion host for cluster access?
- Will you need connectivity to other Azure services (ACR, Key Vau lt, etc.)?

Additional Requirements:
- Do you need monitoring/logging enabled (Azure Monitor, Log Analytics)?
- Any specific compliance or security requirements?
- Should the module include RBAC role assignments?