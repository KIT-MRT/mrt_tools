#pragma once

#include <diagnostic_updater/diagnostic_updater.h> //@diagnostics@
#include <diagnostic_updater/publisher.h>          //@diagnostics@
#include <dynamic_reconfigure/server.h>
#include <ros/ros.h>
#include <tf2_ros/transform_broadcaster.h> //@tf@
#include <tf2_ros/transform_listener.h>    //@tf@
#include "${pkgname}/${ClassName}Parameters.h"

namespace ${pkgname} {

class ${ClassName} {
public:
    ${ClassName}(ros::NodeHandle, ros::NodeHandle);

private:
    ros::Publisher dummy_pub_;
    ros::Subscriber dummy_sub_;

    ${ClassName}Parameters& params_;

    dynamic_reconfigure::Server<${ClassName}Config> reconfig_srv_; // Dynamic reconfiguration service

    tf2_ros::Buffer tfBuffer_;                     //@tf@
    tf2_ros::TransformListener tfListener_;        //@tf@
    tf2_ros::TransformBroadcaster tf_broadcaster_; //@tf@

    /// Diagnostics                                                                           //@diagnostics@
    diagnostic_updater::Updater updater_;                                                     //@diagnostics@
    // std::unique_ptr<diagnostic_updater::DiagnosedPublisher<std_msgs::Header>> diagnosed_pub_; //@diagnostics@
    diagnostic_msgs::DiagnosticStatus diagnostic_status_;                                     //@diagnostics@

    void setupDiagnostics();                                              //@diagnostics@
    void checkSensorStatus(diagnostic_updater::DiagnosticStatusWrapper&); //@diagnostics@
    void diagnostic_msg(diagnostic_updater::DiagnosticStatusWrapper&);    //@diagnostics@
    void diagnoseError();                                                 //@diagnostics@

    void subCallback(const std_msgs::Header::ConstPtr& msg);
    void reconfigureRequest(${ClassName}Config&, uint32_t);
};

} // namespace ${pkgname}
