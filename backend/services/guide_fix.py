        "next_steps": [
            f"1. Set up AWS account with budget alert for {cost_range}",
            "2. Review prerequisites and gather tools",
            "3. Follow implementation phases in order",
            f"4. Test with {min(100, estimated_users // 10)} concurrent users",
            "5. Monitor CloudWatch metrics closely",
            "6. Scale gradually based on actual usage"
        ],
        
        # ADD PHASES
        "phases": get_implementation_phases(services, project_type, estimated_users)
    }
    
    return guide
