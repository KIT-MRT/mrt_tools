#include "${class_name}.hpp"
#include <utils_ros/ros_console.hpp>

namespace ${pkgname} {

${ClassName}::${ClassName}(ros::NodeHandle node_handle, ros::NodeHandle private_node_handle)
        : reconfigSrv_{private_node_handle}, params_{private_node_handle}
          , tfListener_{tfBuffer_} //@tf@
{

    /**
     * Initialization
     */
    utils_ros::setLoggerLevel(private_node_handle);
    params_.fromParamServer();
    setupDiagnostics(); //@diagnostics@

    /**
     * Set up dynamic reconfiguration
     */
    reconfigSrv_.setCallback(boost::bind(&${ClassName}::reconfigureRequest, this, _1, _2));

    /**
     * Publishers & subscriber
     */
    // A diagnosed pub can be used for message types with header.                                //@diagnostics@
    // This adds a diagnostics message for the frequency to this topic                           //@diagnostics@
    // diagnosed_pub_ = std::make_unique<diagnostic_updater::DiagnosedPublisher<std_msgs::Header>>( //@diagnostics@
    //     private_node_handle.advertise<std_msgs::Header>(params_.diag_pub_msg_name,               //@diagnostics@
    //                                                     params_.msg_queue_size),                 //@diagnostics@
    //     updater_,                                                                                //@diagnostics@
    //     diagnostic_updater::FrequencyStatusParam(&params_.diagnostic_updater_rate,		   //@diagnostics@
    //                                              &params_.diagnostic_updater_rate,              //@diagnostics@
    //                                              params_.diagnostic_updater_rate_tolerance, 5), //@diagnostics@
    //     diagnostic_updater::TimeStampStatusParam());                                            //@diagnostics@

    dummyPub_ = private_node_handle.advertise<std_msgs::Header>(params_.publisher_msg_name, params_.msg_queue_size);
    // Instantiate subscriber last, to assure all objects are initialised when first message is received.
    dummySub_ = private_node_handle.subscribe(params_.subscriber_msg_name, params_.msg_queue_size,
                                               &${ClassName}::subCallback, this, ros::TransportHints().tcpNoDelay());

    utils_ros::showNodeInfo();
}

/*
 * Use const ConstPtr for your callbacks.
 * The 'const' assures that you can not edit incoming messages.
 * The Ptr type guarantees zero copy transportation within nodelets.
 */
void ${ClassName}::subCallback(const std_msgs::Header::ConstPtr& msg) {

    // do your stuff here...
    std_msgs::Header new_msg = *msg;
    dummyPub_.publish(new_msg);
    // diagnosed_pub_->publish(new_msg);                                 //@diagnostics@
                                                                      //@diagnostics@
    diagnosticStatus_.message = "Valid loop";                        //@diagnostics@
    diagnosticStatus_.level = diagnostic_msgs::DiagnosticStatus::OK; //@diagnostics@
    // The updater will take care of publishing at a throttled rate   //@diagnostics@
    // When calling update, all updater callbacks (defined in setupDiagnostics) will be run //@diagnostics@
    updater_.update(); //@diagnostics@
}

/**
  * This callback is called whenever a change was made in the dynamic_reconfigure window
*/
void ${ClassName}::reconfigureRequest(${ClassName}Config& config, uint32_t level) {
    params_.fromConfig(config);
}

/*           //@diagnostics@
 * Setup the Diagnostic Updater  //@diagnostics@
 */           //@diagnostics@
void ${ClassName}::setupDiagnostics() { //@diagnostics@
                                       // Give a unique hardware id //@diagnostics@
    diagnosticStatus_.hardware_id = params_.diagnostic_updater_hardware_id; //@diagnostics@
    diagnosticStatus_.message = "Starting...";                              //@diagnostics@
    diagnosticStatus_.level = diagnostic_msgs::DiagnosticStatus::STALE;     //@diagnostics@
    updater_.setHardwareID(params_.diagnostic_updater_hardware_id);          //@diagnostics@
    //@diagnostics@
    // Add further callbacks (or unittests) that should be called regularly //@diagnostics@
    updater_.add("${ClassName} Sensor Status", this, &${ClassName}::checkSensorStatus); //@diagnostics@
    //@diagnostics@
    updater_.force_update(); //@diagnostics@
} //@diagnostics@
//@diagnostics@
void ${ClassName}::checkSensorStatus(diagnostic_updater::DiagnosticStatusWrapper& status_wrapper) { //@diagnostics@
    status_wrapper.summary(diagnosticStatus_);                                                    //@diagnostics@
} //@diagnostics@

} // namespace ${pkgname}
