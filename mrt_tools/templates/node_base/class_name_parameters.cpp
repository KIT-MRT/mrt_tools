#include "${class_name}_parameters.h"

#include <utils_ros/node_handle.hpp>

namespace ${pkgname} {

${ClassName}Parameters& ${ClassName}Parameters::getInstance() {

    static ${ClassName}Parameters p;
    return p;
}

void ${ClassName}Parameters::fromNodeHandle(const ros::NodeHandle& node_handle) {
    using namespace utils_ros;

    getParam(node_handle, STR(verbosity), verbosity);
    getParam(node_handle, STR(msg_queue_size), msg_queue_size);

    getParam(node_handle, STR(subscriber_msg_name), subscriber_msg_name);
    getParam(node_handle, STR(publisher_msg_name), publisher_msg_name);

    getParam(node_handle, STR(diag_pub_msg_name), diag_pub_msg_name);                                 //@diagnostics@
    getParam(node_handle, STR(diagnostic_updater_rate_tolerance), diagnostic_updater_rate_tolerance); //@diagnostics@
    getParam(node_handle, STR(diagnostic_updater_hardware_id), diagnostic_updater_hardware_id);       //@diagnostics@
    getParam(node_handle, STR(diagnostic_updater_name), diagnostic_updater_name);                     //@diagnostics@
    getParam(node_handle, STR(diagnostic_updater_rate), diagnostic_updater_rate);                     //@diagnostics@

    getParam(node_handle, STR(dummy), dummy);
}
} // namespace ${pkgname}
