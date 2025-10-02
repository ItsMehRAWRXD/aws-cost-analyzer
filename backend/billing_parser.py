#!/usr/bin/env python3
"""
Enhanced AWS Billing Parser
Advanced cost analysis with AI-powered optimization recommendations
"""

import json
import csv
import pandas as pd
from io import StringIO, BytesIO
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncio
import aiohttp
import os
from dataclasses import dataclass

@dataclass
class CostRecommendation:
    title: str
    description: str
    potential_savings: float
    priority: str  # "High", "Medium", "Low"
    implementation_effort: str  # "Easy", "Medium", "Complex"
    category: str  # "Compute", "Storage", "Network", "Database"

@dataclass
class CostAnalysis:
    total_cost: float
    services: Dict[str, float]
    recommendations: List[CostRecommendation]
    potential_savings: float
    optimized_cost: float
    analysis_date: datetime
    confidence_score: float

class EnhancedBillingParser:
    def __init__(self):
        self.aws_pricing_cache = {}
        self.optimization_rules = self._load_optimization_rules()
    
    def _load_optimization_rules(self) -> Dict[str, Any]:
        """Load optimization rules and patterns"""
        return {
            "ec2": {
                "reserved_instance_savings": 0.15,
                "spot_instance_savings": 0.20,
                "rightsizing_savings": 0.12,
                "scheduled_shutdown_savings": 0.08
            },
            "s3": {
                "storage_class_optimization": 0.10,
                "lifecycle_policy_savings": 0.15,
                "compression_savings": 0.05
            },
            "rds": {
                "reserved_instance_savings": 0.18,
                "rightsizing_savings": 0.10,
                "storage_optimization": 0.08
            },
            "lambda": {
                "memory_optimization": 0.15,
                "timeout_optimization": 0.05
            },
            "cloudfront": {
                "cache_optimization": 0.12,
                "price_class_optimization": 0.08
            }
        }
    
    async def analyze_costs(
        self,
        monthly_bill: float,
        services: List[str],
        region: str = "us-east-1",
        workload_type: str = "web",
        user_plan: str = "starter"
    ) -> Dict[str, Any]:
        """Perform comprehensive cost analysis"""
        
        # Calculate base metrics
        potential_savings = self._calculate_potential_savings(
            monthly_bill, services, workload_type
        )
        optimized_cost = monthly_bill - potential_savings
        wasted_spend = monthly_bill * 0.22  # Industry average
        
        # Generate recommendations based on services and workload
        recommendations = self._generate_recommendations(
            monthly_bill, services, workload_type, user_plan
        )
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(
            services, workload_type, user_plan
        )
        
        # Simulate service breakdown
        service_breakdown = self._simulate_service_breakdown(
            monthly_bill, services
        )
        
        return {
            "current_bill": monthly_bill,
            "potential_savings": potential_savings,
            "optimized_bill": optimized_cost,
            "wasted_spend": wasted_spend,
            "recommendations": [
                {
                    "title": rec.title,
                    "description": rec.description,
                    "potential_savings": rec.potential_savings,
                    "priority": rec.priority,
                    "implementation_effort": rec.implementation_effort,
                    "category": rec.category
                }
                for rec in recommendations
            ],
            "service_breakdown": service_breakdown,
            "confidence_score": confidence_score,
            "analysis_date": datetime.now().isoformat(),
            "region": region,
            "workload_type": workload_type
        }
    
    async def parse_billing_file(
        self, 
        file_content: bytes, 
        filename: str
    ) -> Dict[str, Any]:
        """Parse uploaded billing file"""
        try:
            if filename.endswith('.json'):
                return await self._parse_json_billing(file_content)
            elif filename.endswith('.csv'):
                return await self._parse_csv_billing(file_content)
            elif filename.endswith('.xlsx'):
                return await self._parse_excel_billing(file_content)
            else:
                raise ValueError("Unsupported file format")
        except Exception as e:
            raise Exception(f"Failed to parse billing file: {str(e)}")
    
    async def _parse_json_billing(self, content: bytes) -> Dict[str, Any]:
        """Parse JSON billing data"""
        try:
            data = json.loads(content.decode('utf-8'))
            
            # Handle different JSON structures
            if isinstance(data, dict):
                if "total" in data:
                    return self._analyze_from_total(data)
                elif "bills" in data:
                    return self._analyze_from_bills(data["bills"])
                elif "resultsByTime" in data:
                    return self._analyze_from_cost_explorer(data)
                else:
                    return self._analyze_generic_json(data)
            else:
                raise ValueError("Invalid JSON structure")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {str(e)}")
    
    async def _parse_csv_billing(self, content: bytes) -> Dict[str, Any]:
        """Parse CSV billing data"""
        try:
            text = content.decode('utf-8')
            df = pd.read_csv(StringIO(text))
            
            # Identify cost and service columns
            cost_columns = [col for col in df.columns if 'cost' in col.lower() or 'amount' in col.lower()]
            service_columns = [col for col in df.columns if 'service' in col.lower() or 'product' in col.lower()]
            
            if not cost_columns:
                raise ValueError("No cost columns found in CSV")
            
            total_cost = 0
            services = {}
            
            for _, row in df.iterrows():
                cost_value = 0
                for cost_col in cost_columns:
                    if pd.notna(row[cost_col]):
                        cost_value += float(row[cost_col])
                
                service_name = "Unknown"
                if service_columns:
                    for service_col in service_columns:
                        if pd.notna(row[service_col]):
                            service_name = str(row[service_col])
                            break
                
                total_cost += cost_value
                services[service_name] = services.get(service_name, 0) + cost_value
            
            return await self.analyze_costs(
                total_cost, 
                list(services.keys()),
                workload_type="mixed"
            )
        except Exception as e:
            raise ValueError(f"Failed to parse CSV: {str(e)}")
    
    async def _parse_excel_billing(self, content: bytes) -> Dict[str, Any]:
        """Parse Excel billing data"""
        try:
            df = pd.read_excel(BytesIO(content))
            
            # Similar logic to CSV parsing
            cost_columns = [col for col in df.columns if 'cost' in col.lower() or 'amount' in col.lower()]
            service_columns = [col for col in df.columns if 'service' in col.lower() or 'product' in col.lower()]
            
            if not cost_columns:
                raise ValueError("No cost columns found in Excel file")
            
            total_cost = 0
            services = {}
            
            for _, row in df.iterrows():
                cost_value = 0
                for cost_col in cost_columns:
                    if pd.notna(row[cost_col]):
                        cost_value += float(row[cost_col])
                
                service_name = "Unknown"
                if service_columns:
                    for service_col in service_columns:
                        if pd.notna(row[service_col]):
                            service_name = str(row[service_col])
                            break
                
                total_cost += cost_value
                services[service_name] = services.get(service_name, 0) + cost_value
            
            return await self.analyze_costs(
                total_cost,
                list(services.keys()),
                workload_type="mixed"
            )
        except Exception as e:
            raise ValueError(f"Failed to parse Excel file: {str(e)}")
    
    def _calculate_potential_savings(
        self, 
        monthly_bill: float, 
        services: List[str], 
        workload_type: str
    ) -> float:
        """Calculate potential savings based on services and workload"""
        base_savings_rate = 0.25  # 25% base savings
        
        # Adjust based on services
        service_multipliers = {
            "EC2": 1.2,  # Higher savings potential
            "S3": 1.1,
            "RDS": 1.3,
            "Lambda": 0.8,  # Lower savings potential
            "CloudFront": 1.0
        }
        
        # Adjust based on workload type
        workload_multipliers = {
            "web": 1.0,
            "data": 1.2,
            "ml": 1.1,
            "storage": 1.3,
            "compute": 1.4
        }
        
        multiplier = 1.0
        for service in services:
            service_key = service.upper().split()[0]  # Get first word
            if service_key in service_multipliers:
                multiplier *= service_multipliers[service_key]
        
        if workload_type in workload_multipliers:
            multiplier *= workload_multipliers[workload_type]
        
        return monthly_bill * base_savings_rate * min(multiplier, 1.5)  # Cap at 50% savings
    
    def _generate_recommendations(
        self, 
        monthly_bill: float, 
        services: List[str], 
        workload_type: str,
        user_plan: str
    ) -> List[CostRecommendation]:
        """Generate optimization recommendations"""
        recommendations = []
        
        # Base recommendations
        recommendations.extend([
            CostRecommendation(
                title="Reserved Instances",
                description="Switch to 1-year Reserved Instances for steady-state workloads",
                potential_savings=monthly_bill * 0.15,
                priority="High",
                implementation_effort="Medium",
                category="Compute"
            ),
            CostRecommendation(
                title="Right-size EC2 Instances",
                description="Your instances are over-provisioned. Downsize to save costs",
                potential_savings=monthly_bill * 0.12,
                priority="High",
                implementation_effort="Easy",
                category="Compute"
            ),
            CostRecommendation(
                title="S3 Storage Optimization",
                description="Move infrequently accessed data to cheaper storage classes",
                potential_savings=monthly_bill * 0.08,
                priority="Medium",
                implementation_effort="Easy",
                category="Storage"
            )
        ])
        
        # Service-specific recommendations
        for service in services:
            service_lower = service.lower()
            
            if "ec2" in service_lower or "compute" in service_lower:
                if workload_type == "compute":
                    recommendations.append(CostRecommendation(
                        title="Spot Instances",
                        description="Use Spot Instances for fault-tolerant workloads",
                        potential_savings=monthly_bill * 0.20,
                        priority="High",
                        implementation_effort="Complex",
                        category="Compute"
                    ))
            
            if "s3" in service_lower or "storage" in service_lower:
                recommendations.append(CostRecommendation(
                    title="S3 Lifecycle Policies",
                    description="Implement lifecycle policies to automatically move old data",
                    potential_savings=monthly_bill * 0.10,
                    priority="Medium",
                    implementation_effort="Easy",
                    category="Storage"
                ))
            
            if "rds" in service_lower or "database" in service_lower:
                recommendations.append(CostRecommendation(
                    title="RDS Reserved Instances",
                    description="Purchase Reserved Instances for your database workloads",
                    potential_savings=monthly_bill * 0.18,
                    priority="High",
                    implementation_effort="Medium",
                    category="Database"
                ))
        
        # Plan-specific recommendations
        if user_plan in ["professional", "enterprise"]:
            recommendations.append(CostRecommendation(
                title="Auto Scaling Groups",
                description="Implement auto scaling to match demand",
                potential_savings=monthly_bill * 0.10,
                priority="Medium",
                implementation_effort="Complex",
                category="Compute"
            ))
        
        # Sort by potential savings
        recommendations.sort(key=lambda x: x.potential_savings, reverse=True)
        
        return recommendations[:10]  # Return top 10 recommendations
    
    def _calculate_confidence_score(
        self, 
        services: List[str], 
        workload_type: str,
        user_plan: str
    ) -> float:
        """Calculate confidence score for the analysis"""
        base_score = 0.7
        
        # Increase confidence with more services
        service_bonus = min(len(services) * 0.05, 0.2)
        
        # Increase confidence with specific workload types
        workload_bonus = {
            "web": 0.1,
            "data": 0.15,
            "ml": 0.05,
            "storage": 0.1,
            "compute": 0.15
        }.get(workload_type, 0.05)
        
        # Increase confidence with higher-tier plans
        plan_bonus = {
            "starter": 0.0,
            "professional": 0.1,
            "enterprise": 0.15
        }.get(user_plan, 0.0)
        
        return min(base_score + service_bonus + workload_bonus + plan_bonus, 0.95)
    
    def _simulate_service_breakdown(
        self, 
        monthly_bill: float, 
        services: List[str]
    ) -> Dict[str, float]:
        """Simulate service cost breakdown"""
        if not services:
            return {
                "EC2": monthly_bill * 0.4,
                "S3": monthly_bill * 0.2,
                "RDS": monthly_bill * 0.15,
                "Lambda": monthly_bill * 0.1,
                "CloudFront": monthly_bill * 0.1,
                "Other": monthly_bill * 0.05
            }
        
        # Distribute costs based on provided services
        service_costs = {}
        remaining_bill = monthly_bill
        
        # Common service cost distributions
        service_distributions = {
            "EC2": 0.4,
            "S3": 0.2,
            "RDS": 0.15,
            "Lambda": 0.1,
            "CloudFront": 0.1,
            "DynamoDB": 0.08,
            "EBS": 0.12,
            "ELB": 0.05,
            "Route53": 0.02,
            "CloudWatch": 0.03
        }
        
        for service in services:
            service_key = service.upper().split()[0]
            if service_key in service_distributions:
                cost = monthly_bill * service_distributions[service_key]
                service_costs[service] = cost
                remaining_bill -= cost
        
        # Distribute remaining cost
        if remaining_bill > 0:
            service_costs["Other Services"] = remaining_bill
        
        return service_costs
    
    def _analyze_from_total(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze from total cost data"""
        total = data.get("total", 0)
        services = data.get("services", {})
        return {
            "total_cost": total,
            "services": services,
            "analysis_type": "total_based"
        }
    
    def _analyze_from_bills(self, bills: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze from bills array"""
        total = 0
        services = {}
        
        for bill in bills:
            cost = float(bill.get("amount", 0))
            service = bill.get("service", "Unknown")
            total += cost
            services[service] = services.get(service, 0) + cost
        
        return {
            "total_cost": total,
            "services": services,
            "analysis_type": "bills_based"
        }
    
    def _analyze_from_cost_explorer(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze from AWS Cost Explorer format"""
        total = 0
        services = {}
        
        for result in data.get("resultsByTime", []):
            for group in result.get("groups", []):
                for metric in group.get("metrics", {}).values():
                    amount = float(metric.get("amount", 0))
                    total += amount
                    
                    # Extract service from group keys
                    service = group.get("keys", ["Unknown"])[0]
                    services[service] = services.get(service, 0) + amount
        
        return {
            "total_cost": total,
            "services": services,
            "analysis_type": "cost_explorer"
        }
    
    def _analyze_generic_json(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze generic JSON structure"""
        total = 0
        services = {}
        
        for key, value in data.items():
            if isinstance(value, (int, float)):
                total += value
                services[key] = value
        
        return {
            "total_cost": total,
            "services": services,
            "analysis_type": "generic"
        }
