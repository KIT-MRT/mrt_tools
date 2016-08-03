#include "${class_name}.hpp"
#include <nodelet/nodelet.h>
#include <pluginlib/class_list_macros.h>

namespace ${pkgname} {

class ${ClassName}Nodelet : public nodelet::Nodelet {

    virtual void onInit();
    boost::shared_ptr<${ClassName}> m_;
};

void ${ClassName}Nodelet::onInit() {
    m_.reset(new ${ClassName}(getNodeHandle(), getPrivateNodeHandle()));
}

} // namespace ${pkgname}

PLUGINLIB_DECLARE_CLASS(${pkgname}, ${ClassName}Nodelet, ${pkgname}::${ClassName}Nodelet, nodelet::Nodelet);
