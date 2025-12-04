package com.project.JobbTren.dto;

import lombok.Data;

import java.util.List;

@Data
public class AnalyzeResponse {
    private List<String> skillsMatch;
    private List<String> missingSkills;
    private double matchScore;
}
