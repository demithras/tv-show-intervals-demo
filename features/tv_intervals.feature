Feature: TV Program 15-Minute Interval Calculation
  As a TV scheduling system
  I want to automatically calculate 15-minute intervals for programs
  So that I can track program duration in standardized time blocks

  Background:
    Given the database is clean

  Scenario: Program with same start and end time has zero intervals
    Given I have a program "Morning News" that runs from "09:00" to "09:00"
    When I insert the program into the database
    Then the program "Morning News" should have 0 intervals

  Scenario: Program shorter than 15 minutes has zero intervals
    Given I have a program "Weather Update" that runs from "12:00" to "12:10"
    When I insert the program into the database
    Then the program "Weather Update" should have 0 intervals

  Scenario: Program exactly 15 minutes long has one interval
    Given I have a program "Quick News" that runs from "18:00" to "18:15"
    When I insert the program into the database
    Then the program "Quick News" should have 1 intervals

  Scenario: Program exactly 30 minutes long has two intervals
    Given I have a program "Sports Update" that runs from "20:00" to "20:30"
    When I insert the program into the database
    Then the program "Sports Update" should have 2 intervals

  Scenario: Program spanning multiple intervals with partial duration
    Given I have a program "Movie Night" that runs from "21:00" to "21:40"
    When I insert the program into the database
    Then the program "Movie Night" should have 2 intervals

  Scenario: Overnight program crossing midnight
    Given I have a program "Late Night Talk" that runs from "23:30" to "00:15"
    When I insert the program into the database
    Then the program "Late Night Talk" should have 3 intervals

  Scenario: Overnight program with longer duration
    Given I have a program "Midnight Movie" that runs from "23:00" to "01:30"
    When I insert the program into the database
    Then the program "Midnight Movie" should have 10 intervals

  Scenario: Multiple programs with different interval counts
    Given I have the following programs:
      | program_name    | start_time | end_time |
      | Morning Show    | 07:00      | 08:00    |
      | News Brief      | 12:00      | 12:05    |
      | Evening Movie   | 20:00      | 22:15    |
      | Night Talk      | 23:45      | 00:30    |
    When I insert all programs into the database
    Then the interval counts should be:
      | program_name    | intervals |
      | Morning Show    | 4         |
      | News Brief      | 0         |
      | Evening Movie   | 9         |
      | Night Talk      | 3         |

  Scenario: Empty database has no intervals
    Given the database is clean
    When I check the program intervals table
    Then there should be 0 rows in the program intervals table

  Scenario: Updating a program recalculates intervals
    Given I have a program "Test Show" that runs from "10:00" to "10:30"
    When I insert the program into the database
    Then the program "Test Show" should have 2 intervals
    When I update the program "Test Show" to run from "10:00" to "11:00"
    Then the program "Test Show" should have 4 intervals

  Scenario: Deleting a program removes its intervals
    Given I have a program "Temporary Show" that runs from "15:00" to "16:00"
    When I insert the program into the database
    Then the program "Temporary Show" should have 4 intervals
    When I delete the program "Temporary Show"
    Then there should be no intervals for program "Temporary Show"

  Scenario: Program name change updates intervals table
    Given I have a program "Old Name" that runs from "14:00" to "14:45"
    When I insert the program into the database
    Then the program "Old Name" should have 3 intervals
    When I rename the program "Old Name" to "New Name"
    Then the program "New Name" should have 3 intervals
    And there should be no intervals for program "Old Name"

  # Boundary Value Tests
  Scenario: Program exactly 14 minutes should have zero intervals
    Given I have a program "Exactly 14 Min" that runs from "10:00" to "10:14"
    When I insert the program into the database
    Then the program "Exactly 14 Min" should have 0 intervals

  Scenario: Program exactly 16 minutes should have one interval
    Given I have a program "Just Over 15 Min" that runs from "10:00" to "10:16"
    When I insert the program into the database
    Then the program "Just Over 15 Min" should have 1 intervals

  Scenario: Program exactly 29 minutes should have one interval
    Given I have a program "Almost 30 Min" that runs from "10:00" to "10:29"
    When I insert the program into the database
    Then the program "Almost 30 Min" should have 1 intervals

  Scenario: Program exactly 31 minutes should have two intervals
    Given I have a program "Just Over 30 Min" that runs from "10:00" to "10:31"
    When I insert the program into the database
    Then the program "Just Over 30 Min" should have 2 intervals

  Scenario: Midnight boundary - program ending exactly at midnight
    Given I have a program "Ends At Midnight" that runs from "23:30" to "00:00"
    When I insert the program into the database
    Then the program "Ends At Midnight" should have 2 intervals

  Scenario: Midnight boundary - program starting exactly at midnight
    Given I have a program "Starts At Midnight" that runs from "00:00" to "00:30"
    When I insert the program into the database
    Then the program "Starts At Midnight" should have 2 intervals

  Scenario: One minute before midnight to one minute after midnight
    Given I have a program "Cross Midnight Brief" that runs from "23:59" to "00:01"
    When I insert the program into the database
    Then the program "Cross Midnight Brief" should have 0 intervals

  Scenario: Very long overnight program - almost full day
    Given I have a program "Almost Full Day" that runs from "00:01" to "00:00"
    When I insert the program into the database
    Then the program "Almost Full Day" should have 95 intervals

  Scenario: Exactly one hour program
    Given I have a program "One Hour Show" that runs from "15:00" to "16:00"
    When I insert the program into the database
    Then the program "One Hour Show" should have 4 intervals

  Scenario: Maximum daily program - full 24 hours
    Given I have a program "Full Day Marathon" that runs from "00:00" to "00:00"
    When I insert the program into the database
    Then the program "Full Day Marathon" should have 0 intervals

  Scenario: Large intervals - 6 hour program
    Given I have a program "Long Movie Block" that runs from "18:00" to "00:00"
    When I insert the program into the database
    Then the program "Long Movie Block" should have 24 intervals

  Scenario: Multiple boundary cases in one test
    Given I have the following programs:
      | program_name      | start_time | end_time |
      | Edge Case 1       | 12:00      | 12:14    |
      | Edge Case 2       | 12:00      | 12:15    |
      | Edge Case 3       | 12:00      | 12:16    |
      | Edge Case 4       | 12:00      | 12:29    |
      | Edge Case 5       | 12:00      | 12:30    |
      | Edge Case 6       | 12:00      | 12:31    |
      | Edge Case 7       | 12:00      | 12:44    |
      | Edge Case 8       | 12:00      | 12:45    |
      | Edge Case 9       | 12:00      | 12:46    |
    When I insert all programs into the database
    Then the interval counts should be:
      | program_name      | intervals |
      | Edge Case 1       | 0         |
      | Edge Case 2       | 1         |
      | Edge Case 3       | 1         |
      | Edge Case 4       | 1         |
      | Edge Case 5       | 2         |
      | Edge Case 6       | 2         |
      | Edge Case 7       | 2         |
      | Edge Case 8       | 3         |
      | Edge Case 9       | 3         |

  # Test scenario for CI/CD validation - will be temporarily modified for testing
  Scenario: CI/CD Test Scenario - Validate comment posting
    Given I have a program "CI Test Program" that runs from "10:00" to "10:30"
    When I insert the program into the database
    Then the program "CI Test Program" should have 2 intervals