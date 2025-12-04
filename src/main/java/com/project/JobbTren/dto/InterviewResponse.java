package com.project.JobbTren.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Getter;
import lombok.Setter;

import java.util.List;

@Getter
@Setter
public class InterviewResponse {

    @JsonProperty("job_keywords")
    private List<String> jobKeywords;
    private List<QAPair> interview;

    @Getter
    @Setter
    public static class QAPair {
        private String question;
        private String answer;
    }

}
