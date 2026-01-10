-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Aug 27, 2025 at 05:41 PM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `foty.ai`
--

-- --------------------------------------------------------

--
-- Table structure for table `aiengine`
--

DROP TABLE IF EXISTS `aiengine`;

CREATE TABLE `aiengine` (
  `engine_id` int(11) NOT NULL,
  `video_id` int(11) DEFAULT NULL,
  `process_date` datetime DEFAULT NULL,
  `status` varchar(50) DEFAULT NULL,
  `model_version` varchar(100) DEFAULT 'Enhanced-YOLO-Shot-Detection-v2.0'
);


-- --------------------------------------------------------

--
-- Table structure for table `custommodels`
--
DROP TABLE IF EXISTS `custommodels`; 
CREATE TABLE `custommodels` (
  `model_id` int(11) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `model_path` varchar(500) DEFAULT NULL,
  `training_date` datetime DEFAULT NULL,
  `model_type` varchar(100) DEFAULT NULL,
  `performance_score` float DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `motionanalysis`
--
DROP TABLE IF EXISTS `motionanalysis`; 
CREATE TABLE `motionanalysis` (
  `analysis_id` int(11) NOT NULL,
  `engine_id` int(11) DEFAULT NULL,
  `technique_score` decimal(5,2) DEFAULT NULL,
  `balance_score` decimal(5,2) DEFAULT NULL,
  `movement_efficiency` decimal(5,2) DEFAULT NULL,
  `kick_count` int(11) DEFAULT 0,
  `total_distance` decimal(10,2) DEFAULT 0.00,
  `shots_detected` int(11) DEFAULT 0,
  `shot_accuracy` decimal(5,2) DEFAULT 0.00
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `performancelog`
--
DROP TABLE IF EXISTS `performancelog`; 
CREATE TABLE `performancelog` (
  `log_id` int(11) NOT NULL,
  `player_id` int(11) DEFAULT NULL,
  `date` date DEFAULT NULL,
  `comment` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `player`
--
DROP TABLE IF EXISTS `player`; 

CREATE TABLE `player` (
  `player_id` int(11) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `age` int(11) DEFAULT NULL,
  `position` varchar(50) DEFAULT NULL,
  `team_name` varchar(255) DEFAULT 'Default Team',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `playermetrics`
--
DROP TABLE IF EXISTS `playermetrics`; 
CREATE TABLE `playermetrics` (
  `metric_id` int(11) NOT NULL,
  `player_id` int(11) DEFAULT NULL,
  `analysis_id` int(11) DEFAULT NULL,
  `speed` decimal(5,2) DEFAULT NULL,
  `stamina` decimal(5,2) DEFAULT NULL,
  `strength` decimal(5,2) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `recommendationengine`
--

DROP TABLE IF EXISTS `recommendationengine`; 

CREATE TABLE `recommendationengine` (
  `engine_id` int(11) NOT NULL,
  `metric_id` int(11) DEFAULT NULL,
  `recommendation_text` text DEFAULT NULL,
  `generated_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `shotanalysis`
--
DROP TABLE IF EXISTS `shotanalysis`; 
CREATE TABLE `shotanalysis` (
  `shot_id` int(11) NOT NULL,
  `metric_id` int(11) DEFAULT NULL,
  `shot_frame` int(11) DEFAULT NULL,
  `shot_speed` decimal(5,2) DEFAULT NULL,
  `shot_direction` decimal(5,2) DEFAULT NULL,
  `shot_type` varchar(50) DEFAULT NULL,
  `shot_quality` decimal(5,2) DEFAULT NULL,
  `technique_rating` decimal(5,2) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `systemuser`
--
DROP TABLE IF EXISTS `systemuser`; 

CREATE TABLE `systemuser` (
  `user_id` int(11) NOT NULL,
  `name` varchar(100) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `password` varchar(255) DEFAULT NULL,
  `role` enum('Admin','Player') DEFAULT NULL,
  `TeamName` varchar(255) DEFAULT NULL,
  `age` int(11) DEFAULT NULL,
  `image` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `trainingadvice`
--
DROP TABLE IF EXISTS `trainingadvice`; 
CREATE TABLE `trainingadvice` (
  `advice_id` int(11) NOT NULL,
  `player_id` int(11) DEFAULT NULL,
  `engine_id` int(11) DEFAULT NULL,
  `advice` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `videoinput`
--
DROP TABLE IF EXISTS `videoinput`; 
CREATE TABLE `videoinput` (
  `video_id` int(11) NOT NULL,
  `player_id` int(11) DEFAULT NULL,
  `upload_time` datetime DEFAULT NULL,
  `file_path` varchar(255) DEFAULT NULL,
  `original_filename` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `aiengine`
--
ALTER TABLE `aiengine`
  ADD PRIMARY KEY (`engine_id`),
  ADD KEY `video_id` (`video_id`);

--
-- Indexes for table `custommodels`
--
ALTER TABLE `custommodels`
  ADD PRIMARY KEY (`model_id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `motionanalysis`
--
ALTER TABLE `motionanalysis`
  ADD PRIMARY KEY (`analysis_id`),
  ADD KEY `engine_id` (`engine_id`);

--
-- Indexes for table `performancelog`
--
ALTER TABLE `performancelog`
  ADD PRIMARY KEY (`log_id`),
  ADD KEY `player_id` (`player_id`);

--
-- Indexes for table `player`
--
ALTER TABLE `player`
  ADD PRIMARY KEY (`player_id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `playermetrics`
--
ALTER TABLE `playermetrics`
  ADD PRIMARY KEY (`metric_id`),
  ADD KEY `player_id` (`player_id`),
  ADD KEY `analysis_id` (`analysis_id`);

--
-- Indexes for table `recommendationengine`
--
ALTER TABLE `recommendationengine`
  ADD PRIMARY KEY (`engine_id`),
  ADD KEY `metric_id` (`metric_id`);

--
-- Indexes for table `shotanalysis`
--
ALTER TABLE `shotanalysis`
  ADD PRIMARY KEY (`shot_id`),
  ADD KEY `metric_id` (`metric_id`);

--
-- Indexes for table `systemuser`
--
ALTER TABLE `systemuser`
  ADD PRIMARY KEY (`user_id`),
  ADD UNIQUE KEY `email` (`email`);

--
-- Indexes for table `trainingadvice`
--
ALTER TABLE `trainingadvice`
  ADD PRIMARY KEY (`advice_id`),
  ADD KEY `player_id` (`player_id`),
  ADD KEY `engine_id` (`engine_id`);

--
-- Indexes for table `videoinput`
--
ALTER TABLE `videoinput`
  ADD PRIMARY KEY (`video_id`),
  ADD KEY `player_id` (`player_id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `aiengine`
--
ALTER TABLE `aiengine`
  MODIFY `engine_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `custommodels`
--
ALTER TABLE `custommodels`
  MODIFY `model_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `motionanalysis`
--
ALTER TABLE `motionanalysis`
  MODIFY `analysis_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `performancelog`
--
ALTER TABLE `performancelog`
  MODIFY `log_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `player`
--
ALTER TABLE `player`
  MODIFY `player_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `playermetrics`
--
ALTER TABLE `playermetrics`
  MODIFY `metric_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `recommendationengine`
--
ALTER TABLE `recommendationengine`
  MODIFY `engine_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `shotanalysis`
--
ALTER TABLE `shotanalysis`
  MODIFY `shot_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `systemuser`
--
ALTER TABLE `systemuser`
  MODIFY `user_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `trainingadvice`
--
ALTER TABLE `trainingadvice`
  MODIFY `advice_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `videoinput`
--
ALTER TABLE `videoinput`
  MODIFY `video_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `aiengine`
--
ALTER TABLE `aiengine`
  ADD CONSTRAINT `aiengine_ibfk_1` FOREIGN KEY (`video_id`) REFERENCES `videoinput` (`video_id`);

--
-- Constraints for table `custommodels`
--
ALTER TABLE `custommodels`
  ADD CONSTRAINT `custommodels_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `systemuser` (`user_id`);

--
-- Constraints for table `motionanalysis`
--
ALTER TABLE `motionanalysis`
  ADD CONSTRAINT `motionanalysis_ibfk_1` FOREIGN KEY (`engine_id`) REFERENCES `aiengine` (`engine_id`);

--
-- Constraints for table `performancelog`
--
ALTER TABLE `performancelog`
  ADD CONSTRAINT `performancelog_ibfk_1` FOREIGN KEY (`player_id`) REFERENCES `player` (`player_id`);

--
-- Constraints for table `player`
--
ALTER TABLE `player`
  ADD CONSTRAINT `player_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `systemuser` (`user_id`);

--
-- Constraints for table `playermetrics`
--
ALTER TABLE `playermetrics`
  ADD CONSTRAINT `playermetrics_ibfk_1` FOREIGN KEY (`player_id`) REFERENCES `player` (`player_id`),
  ADD CONSTRAINT `playermetrics_ibfk_2` FOREIGN KEY (`analysis_id`) REFERENCES `motionanalysis` (`analysis_id`);

--
-- Constraints for table `recommendationengine`
--
ALTER TABLE `recommendationengine`
  ADD CONSTRAINT `recommendationengine_ibfk_1` FOREIGN KEY (`metric_id`) REFERENCES `playermetrics` (`metric_id`);

--
-- Constraints for table `shotanalysis`
--
ALTER TABLE `shotanalysis`
  ADD CONSTRAINT `shotanalysis_ibfk_1` FOREIGN KEY (`metric_id`) REFERENCES `playermetrics` (`metric_id`);

--
-- Constraints for table `trainingadvice`
--
ALTER TABLE `trainingadvice`
  ADD CONSTRAINT `trainingadvice_ibfk_1` FOREIGN KEY (`player_id`) REFERENCES `player` (`player_id`),
  ADD CONSTRAINT `trainingadvice_ibfk_2` FOREIGN KEY (`engine_id`) REFERENCES `recommendationengine` (`engine_id`);

--
-- Constraints for table `videoinput`
--
ALTER TABLE `videoinput`
  ADD CONSTRAINT `videoinput_ibfk_1` FOREIGN KEY (`player_id`) REFERENCES `player` (`player_id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
