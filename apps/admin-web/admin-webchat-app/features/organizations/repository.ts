import { organizations } from "./data";export const listOrganizations=()=>organizations;export const getOrganizationById=(id:string)=>organizations.find(x=>x.id===id);
